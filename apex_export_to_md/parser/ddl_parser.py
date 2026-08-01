"""Parser plików DDL (SQL) — wyciąga strukturę tabel, widoków, pakietów, procedur, sekwencji.

Parsuje typowe instrukcje CREATE TABLE, CREATE VIEW, CREATE PACKAGE,
CREATE PROCEDURE/FUNCTION, CREATE SEQUENCE, ALTER TABLE, COMMENT ON.
"""
from __future__ import annotations
import logging
import re
from pathlib import Path

from apex_export_to_md.models import (
    DDLSchema, DDLTable, DDLColumn, DDLConstraint, DDLView,
    DDLPackage, DDLProcedure, DDLSequence, DDLIndex, DDLTrigger,
)

logger = logging.getLogger(__name__)


def parse_ddl_file(path: Path) -> DDLSchema:
    """Parsuj plik DDL i zwróć obiekt DDLSchema."""
    content = path.read_text(encoding="utf-8", errors="replace")
    schema = DDLSchema()
    schema.raw_content = content
    schema.source_schema = _detect_source_schema(content)

    schema.tables = _parse_tables(content)
    schema.views = _parse_views(content)
    schema.packages = _parse_packages(content)
    schema.procedures = _parse_procedures(content)
    schema.sequences = _parse_sequences(content)
    schema.indexes = _parse_indexes(content)
    schema.triggers = _parse_triggers(content)

    # Komentarze do tabel i kolumn
    _parse_comments(content, schema)

    # Klucze obce (ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY)
    _parse_alter_constraints(content, schema)

    logger.info("DDL: %d tabel, %d widoków, %d pakietów, %d procedur, %d sekwencji, "
                "%d indeksów, %d triggerów",
                len(schema.tables), len(schema.views), len(schema.packages),
                len(schema.procedures), len(schema.sequences),
                len(schema.indexes), len(schema.triggers))
    return schema


def _detect_source_schema(content: str) -> str:
    """Wykryj nazwę schematu źródłowego z DDL.

    Najpewniejszym źródłem jest prefiks schematu w nagłówku
    CREATE TABLE "SCHEMA"."TABELA" (zawsze cytowany przez DBMS_METADATA).
    Jeśli w pliku nie ma żadnej tabeli (np. same widoki), próbujemy
    wykryć schemat z odwołań do sekwencji w klauzuli DEFAULT/NEXTVAL —
    zarówno w wersji w pełni cytowanej ("SCHEMA"."SEQ"."NEXTVAL"), jak
    i niecytowanej (SCHEMA.SEQ.NEXTVAL), używanej przez starsze wzorce
    kolumn auto-increment w APEX.
    """
    match = re.search(r'CREATE\s+TABLE\s+"(\w+)"\.', content, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r'"?(\w+)"?\s*\.\s*"?\w+"?\s*\.\s*"?NEXTVAL"?', content, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _parse_tables(content: str) -> list[DDLTable]:
    """Wyciągnij CREATE TABLE z treścią kolumn.

    Obsługuje zarówno nazwy proste ("NAZWA"), jak i kwalifikowane
    dowolnym schematem ("SCHEMAT"."NAZWA"). Nawiasy listy kolumn są
    dopasowywane przez liczenie głębokości (nie regexem), bo mogą
    zawierać zagnieżdżone nawiasy (np. STORAGE(...)), a po zamknięciu
    listy kolumn może wystąpić dodatkowa klauzula (SEGMENT CREATION,
    TABLESPACE...) przed właściwym średnikiem kończącym instrukcję.
    """
    tables: list[DDLTable] = []
    header_pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:"[^"]+"\.)?"([^"]+)"\s*\(',
        re.IGNORECASE,
    )
    for header_match in header_pattern.finditer(content):
        table_name = header_match.group(1)
        open_paren_idx = header_match.end() - 1
        close_paren_idx = _find_matching_paren(content, open_paren_idx)
        if close_paren_idx is None:
            continue
        semi_idx = content.find(";", close_paren_idx)
        if semi_idx == -1:
            continue
        body = content[open_paren_idx + 1:close_paren_idx]
        raw_sql = content[header_match.start():semi_idx + 1]
        columns, constraints = _parse_table_body(body)
        tables.append(DDLTable(
            name=table_name,
            columns=columns,
            constraints=constraints,
            raw_sql=raw_sql,
        ))
    return tables


def _find_matching_paren(content: str, open_idx: int) -> int | None:
    """Znajdź indeks nawiasu zamykającego dla nawiasu otwierającego na open_idx."""
    depth = 0
    for i in range(open_idx, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    return None


def _parse_table_body(body: str) -> tuple[list[DDLColumn], list[DDLConstraint]]:
    """Parsuj ciało CREATE TABLE — kolumny i ograniczenia inline."""
    columns: list[DDLColumn] = []
    constraints: list[DDLConstraint] = []

    # Podziel po przecinkach na najwyższym poziomie (uwzględniając nawiasy)
    parts = _split_top_level(body)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Constraint inline (PK/UNIQUE/CHECK/FOREIGN KEY, ta ostatnia z opcjonalnym REFERENCES)
        constraint_match = re.match(
            r'CONSTRAINT\s+"([^"]+)"\s+(PRIMARY\s+KEY|UNIQUE|CHECK|FOREIGN\s+KEY)\s*\(([^)]*)\)'
            r'(?:\s*REFERENCES\s+(?:"[^"]+"\.)?"([^"]+)"\s*\(([^)]*)\))?',
            part, re.IGNORECASE,
        )
        if constraint_match:
            cname = constraint_match.group(1)
            ctype = re.sub(r'\s+', ' ', constraint_match.group(2).upper())
            ccols_raw = constraint_match.group(3)
            ccols = [c.strip().strip('"') for c in ccols_raw.split(",")]
            check_cond = None
            ref_table = None
            ref_col = None
            if ctype == "CHECK":
                check_match = re.search(r'CHECK\s*\((.+)\)', part, re.IGNORECASE | re.DOTALL)
                if check_match:
                    check_cond = check_match.group(1).strip()
            if ctype == "FOREIGN KEY" and constraint_match.group(4):
                ref_table = constraint_match.group(4)
                ref_cols = [c.strip().strip('"') for c in (constraint_match.group(5) or "").split(",")]
                ref_col = ref_cols[0] if ref_cols else None
            constraints.append(DDLConstraint(
                name=cname, type=ctype, columns=ccols, check_condition=check_cond,
                ref_table=ref_table, ref_column=ref_col,
            ))
            # Ustaw PK na kolumnach
            if ctype == "PRIMARY KEY":
                for col in columns:
                    if col.name in ccols:
                        col.primary_key = True
            continue

        # PRIMARY KEY inline (bez CONSTRAINT)
        pk_match = re.match(r'PRIMARY\s+KEY\s*\(([^)]*)\)', part, re.IGNORECASE)
        if pk_match:
            ccols = [c.strip().strip('"') for c in pk_match.group(1).split(",")]
            constraints.append(DDLConstraint(name="", type="PRIMARY KEY", columns=ccols))
            for col in columns:
                if col.name in ccols:
                    col.primary_key = True
            continue

        # Kolumna: "NAZWA" TYP [DEFAULT ...] [NOT NULL] [ENABLE]
        col_match = re.match(r'"([^"]+)"\s+(.+)', part, re.IGNORECASE)
        if col_match:
            col_name = col_match.group(1)
            rest = col_match.group(2).strip()

            # Wyciągnij typ danych (pierwsze słowo lub słowo z nawiasami)
            dtype_match = re.match(
                r'((?:NUMBER|VARCHAR2|CHAR|DATE|TIMESTAMP|CLOB|BLOB|INTEGER|FLOAT)'
                r'(?:\s*\([^)]*\))?)',
                rest, re.IGNORECASE,
            )
            data_type = dtype_match.group(1).strip() if dtype_match else rest.split()[0]

            nullable = "NOT NULL" not in rest.upper()

            # Wykryj kolumnę IDENTITY
            is_identity = False
            identity_def = None
            if "GENERATED" in rest.upper() and "IDENTITY" in rest.upper():
                is_identity = True
                identity_match = re.search(
                    r'(GENERATED\s+.*?AS\s+IDENTITY.*?)(?:\s+NOT\s+NULL|\s+ENABLE|\s*$)',
                    rest, re.IGNORECASE,
                )
                if identity_match:
                    identity_def = identity_match.group(1).strip()

            default_val = None
            if not is_identity:
                default_match = re.search(r'DEFAULT\s+(.+?)(?:\s+NOT\s+NULL|\s+ENABLE|\s*$)', rest, re.IGNORECASE)
                if default_match:
                    default_val = default_match.group(1).strip()

            pk = False
            if re.search(r'PRIMARY\s+KEY', rest, re.IGNORECASE):
                pk = True

            columns.append(DDLColumn(
                name=col_name,
                data_type=data_type,
                nullable=nullable,
                default=default_val,
                primary_key=pk,
                identity=is_identity,
                identity_def=identity_def,
            ))

    return columns, constraints


def _split_top_level(text: str) -> list[str]:
    """Podziel tekst po przecinkach, ignorując zawartość nawiasów."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def _parse_views(content: str) -> list[DDLView]:
    """Wyciągnij CREATE VIEW."""
    views: list[DDLView] = []
    pattern = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?(?:EDITIONABLE\s+)?VIEW\s+(?:"[^"]+"\.)?"([^"]+)"\s*'
        r'(?:\([^)]*\)\s*)?AS\s+(.*?)(?:;\s*$|\n\s*\n)',
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    for match in pattern.finditer(content):
        views.append(DDLView(name=match.group(1), sql=match.group(2).strip()))
    return views


def _parse_packages(content: str) -> list[DDLPackage]:
    """Wyciągnij CREATE PACKAGE (spec + body, połączone w jeden obiekt)."""
    packages: list[DDLPackage] = []
    # Najpierw specyfikacje (CREATE PACKAGE ... AS ... END;) — bez BODY
    spec_pattern = re.compile(
        r'create\s+or\s+replace\s+(?:EDITIONABLE\s+)?PACKAGE\s+(?!BODY\b)'
        r'(?:"[^"]+"\.)?"?(\w+)"?\s+AS\s+(.*?)END\s+\1\s*;',
        re.DOTALL | re.IGNORECASE,
    )
    for match in spec_pattern.finditer(content):
        packages.append(DDLPackage(name=match.group(1), code=match.group(2).strip()))

    # Następnie body (CREATE PACKAGE BODY ... AS ... END;) — dołącz do istniejącego
    body_pattern = re.compile(
        r'create\s+or\s+replace\s+(?:EDITIONABLE\s+)?PACKAGE\s+BODY\s+'
        r'(?:"[^"]+"\.)?"?(\w+)"?\s+AS\s+(.*?)END\s+\1\s*;',
        re.DOTALL | re.IGNORECASE,
    )
    pkg_map = {p.name.upper(): p for p in packages}
    seen_bodies: set[str] = set()
    for match in body_pattern.finditer(content):
        name = match.group(1)
        name_upper = name.upper()
        if name_upper in seen_bodies:
            logger.warning("DDL: zduplikowany PACKAGE BODY '%s' — pomijam duplikat.", name)
            continue
        seen_bodies.add(name_upper)
        body_code = match.group(2).strip()
        existing = pkg_map.get(name.upper())
        if existing:
            # Połącz spec + body
            existing.code = existing.code + "\n\n-- PACKAGE BODY --\n\n" + body_code
        else:
            # Body bez specyfikacji (rzadki przypadek)
            packages.append(DDLPackage(name=name, code=body_code))

    return packages


def _parse_procedures(content: str) -> list[DDLProcedure]:
    """Wyciągnij samodzielne CREATE PROCEDURE/FUNCTION (nie z pakietu)."""
    procedures: list[DDLProcedure] = []
    pattern = re.compile(
        r'create\s+or\s+replace\s+(?:EDITIONABLE\s+)?(PROCEDURE|FUNCTION)\s+'
        r'(?:"[^"]+"\.)?"?(\w+)"?\s*'
        r'(.*?)END\s+\2\s*;',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        full_code = f"{match.group(1)} {match.group(2)} {match.group(3).strip()}"
        procedures.append(DDLProcedure(name=match.group(2), code=full_code))
    return procedures


def _parse_sequences(content: str) -> list[DDLSequence]:
    """Wyciągnij CREATE SEQUENCE."""
    sequences: list[DDLSequence] = []
    pattern = re.compile(
        r'CREATE\s+SEQUENCE\s+(?:"[^"]+"\.)?"([^"]+)"\s*(.*?);',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        seq_name = match.group(1)
        body = match.group(2)
        raw_sql = match.group(0).strip()

        start = None
        incr = None
        min_val = None
        max_val = None
        cache_size = None

        start_match = re.search(r'START\s+WITH\s+(\d+)', body, re.IGNORECASE)
        if start_match:
            start = start_match.group(1)
        incr_match = re.search(r'INCREMENT\s+BY\s+(\d+)', body, re.IGNORECASE)
        if incr_match:
            incr = incr_match.group(1)
        min_match = re.search(r'MINVALUE\s+(\d+)', body, re.IGNORECASE)
        if min_match:
            min_val = min_match.group(1)
        max_match = re.search(r'MAXVALUE\s+(\d+)', body, re.IGNORECASE)
        if max_match:
            max_val = max_match.group(1)
        cache_match = re.search(r'CACHE\s+(\d+)', body, re.IGNORECASE)
        if cache_match:
            cache_size = cache_match.group(1)

        nocache = bool(re.search(r'NOCACHE', body, re.IGNORECASE))
        noorder = bool(re.search(r'NOORDER', body, re.IGNORECASE))
        nocycle = bool(re.search(r'NOCYCLE', body, re.IGNORECASE))

        sequences.append(DDLSequence(
            name=seq_name,
            start_with=start,
            increment_by=incr,
            min_value=min_val,
            max_value=max_val,
            cache_size=cache_size,
            nocache=nocache,
            noorder=noorder,
            nocycle=nocycle,
            raw_sql=raw_sql,
        ))
    return sequences


def _parse_indexes(content: str) -> list[DDLIndex]:
    """Wyciągnij CREATE [UNIQUE] INDEX ... ON ... (kolumny)."""
    indexes: list[DDLIndex] = []
    pattern = re.compile(
        r'CREATE\s+(UNIQUE\s+)?INDEX\s+(?:"[^"]+"\.)?"([^"]+)"\s+ON\s+'
        r'(?:"[^"]+"\.)?"([^"]+)"\s*\(([^)]*)\)',
        re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        is_unique = bool(match.group(1))
        idx_name = match.group(2)
        table_name = match.group(3)
        columns = [c.strip().strip('"') for c in match.group(4).split(",")]
        indexes.append(DDLIndex(
            name=idx_name,
            table_name=table_name,
            columns=columns,
            unique=is_unique,
            raw_sql=match.group(0).strip(),
        ))
    return indexes


def _extract_trigger_table(header: str) -> str | None:
    """Wyciągnij nazwę tabeli z nagłówka triggera (\"ON <tabela>\")."""
    match = re.search(r'\bON\s+(?:"?\w+"?\.)?"?(\w+)"?', header, re.IGNORECASE)
    return match.group(1) if match else None


def _parse_triggers(content: str) -> list[DDLTrigger]:
    """Wyciągnij CREATE [OR REPLACE] TRIGGER — bloki zakończone samotnym '/'."""
    triggers: list[DDLTrigger] = []
    pattern = re.compile(
        r'create\s+or\s+replace\s+(?:EDITIONABLE\s+)?TRIGGER\s+'
        r'(?:"?\w+"?\.)?"?(\w+)"?\s*(.*?)\n\s*/\s*(?:\n|$)',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        name = match.group(1)
        body = match.group(2)
        full_code = f"CREATE OR REPLACE TRIGGER {name}\n{body.strip()}"
        triggers.append(DDLTrigger(
            name=name,
            table_name=_extract_trigger_table(body),
            code=full_code,
        ))
    return triggers


def _parse_comments(content: str, schema: DDLSchema) -> None:
    """Parsuj COMMENT ON TABLE/COLUMN i przypisz do tabel."""
    table_map = {t.name: t for t in schema.tables}

    # COMMENT ON TABLE
    for match in re.finditer(
        r"COMMENT\s+ON\s+TABLE\s+(?:\"[^\"]+\"\.)?\"([^\"]+)\"\s+IS\s+'((?:[^']|'')*)'",
        content, re.IGNORECASE,
    ):
        tname = match.group(1)
        comment = match.group(2).replace("''", "'")
        if tname in table_map:
            table_map[tname].comment = comment
        else:
            # Może to widok
            for v in schema.views:
                if v.name == tname:
                    v.comment = comment
                    break

    # COMMENT ON COLUMN
    for match in re.finditer(
        r"COMMENT\s+ON\s+COLUMN\s+(?:\"[^\"]+\"\.)?\"([^\"]+)\"\.\"([^\"]+)\"\s+IS\s+'((?:[^']|'')*)'",
        content, re.IGNORECASE,
    ):
        tname = match.group(1)
        cname = match.group(2)
        comment = match.group(3).replace("''", "'")
        if tname in table_map:
            table_map[tname].column_comments[cname] = comment


def _parse_alter_constraints(content: str, schema: DDLSchema) -> None:
    """Parsuj ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY."""
    table_map = {t.name: t for t in schema.tables}

    pattern = re.compile(
        r'ALTER\s+TABLE\s+(?:"[^"]+"\.)?"([^"]+)"\s+ADD\s+CONSTRAINT\s+"([^"]+)"\s+'
        r'FOREIGN\s+KEY\s*\("([^"]+)"\)\s*REFERENCES\s+(?:"[^"]+"\.)?"([^"]+)"\s*\("([^"]+)"\)',
        re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        tname = match.group(1)
        cname = match.group(2)
        fk_col = match.group(3)
        ref_table = match.group(4)
        ref_col = match.group(5)
        if tname in table_map:
            table_map[tname].constraints.append(DDLConstraint(
                name=cname,
                type="FOREIGN KEY",
                columns=[fk_col],
                ref_table=ref_table,
                ref_column=ref_col,
            ))
