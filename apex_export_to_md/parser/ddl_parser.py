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
    DDLPackage, DDLProcedure, DDLSequence,
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

    # Komentarze do tabel i kolumn
    _parse_comments(content, schema)

    # Klucze obce (ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY)
    _parse_alter_constraints(content, schema)

    logger.info("DDL: %d tabel, %d widoków, %d pakietów, %d procedur, %d sekwencji",
                len(schema.tables), len(schema.views), len(schema.packages),
                len(schema.procedures), len(schema.sequences))
    return schema


def _detect_source_schema(content: str) -> str:
    """Wykryj nazwę schematu źródłowego z referencji w DDL (np. \"DAW\".\"SEQ\")."""
    match = re.search(r'"(\w+)"\."\w+"\."NEXTVAL"', content, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _parse_tables(content: str) -> list[DDLTable]:
    """Wyciągnij CREATE TABLE z treścią kolumn."""
    tables: list[DDLTable] = []
    # Wzorzec: CREATE TABLE "NAZWA" (\n...\n) ;
    pattern = re.compile(
        r'CREATE\s+TABLE\s+"([^"]+)"\s*\(\s*(.*?)\)\s*;',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        table_name = match.group(1)
        body = match.group(2)
        raw_sql = match.group(0)
        columns, constraints = _parse_table_body(body)
        tables.append(DDLTable(
            name=table_name,
            columns=columns,
            constraints=constraints,
            raw_sql=raw_sql,
        ))
    return tables


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

        # Constraint inline
        constraint_match = re.match(
            r'CONSTRAINT\s+"([^"]+)"\s+(PRIMARY\s+KEY|UNIQUE|CHECK)\s*\(([^)]*)\)',
            part, re.IGNORECASE,
        )
        if constraint_match:
            cname = constraint_match.group(1)
            ctype = constraint_match.group(2).upper()
            ccols_raw = constraint_match.group(3)
            ccols = [c.strip().strip('"') for c in ccols_raw.split(",")]
            check_cond = None
            if ctype == "CHECK":
                check_match = re.search(r'CHECK\s*\((.+)\)', part, re.IGNORECASE | re.DOTALL)
                if check_match:
                    check_cond = check_match.group(1).strip()
            constraints.append(DDLConstraint(
                name=cname, type=ctype, columns=ccols, check_condition=check_cond,
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
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?(?:EDITIONABLE\s+)?VIEW\s+"([^"]+)"\s*'
        r'(?:\([^)]*\)\s*)?AS\s+(.*?)(?:;\s*$|\n\s*\n)',
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    for match in pattern.finditer(content):
        views.append(DDLView(name=match.group(1), sql=match.group(2).strip()))
    return views


def _parse_packages(content: str) -> list[DDLPackage]:
    """Wyciągnij CREATE PACKAGE (spec)."""
    packages: list[DDLPackage] = []
    pattern = re.compile(
        r'create\s+or\s+replace\s+PACKAGE\s+(?:\w+\s+)?(\w+)\s+AS\s+(.*?)END\s+\1\s*;',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        packages.append(DDLPackage(name=match.group(1), code=match.group(2).strip()))
    return packages


def _parse_procedures(content: str) -> list[DDLProcedure]:
    """Wyciągnij samodzielne CREATE PROCEDURE/FUNCTION (nie z pakietu)."""
    procedures: list[DDLProcedure] = []
    pattern = re.compile(
        r'create\s+or\s+replace\s+(PROCEDURE|FUNCTION)\s+(\w+)\s*'
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
        r'CREATE\s+SEQUENCE\s+"([^"]+)"\s*(.*?);',
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


def _parse_comments(content: str, schema: DDLSchema) -> None:
    """Parsuj COMMENT ON TABLE/COLUMN i przypisz do tabel."""
    table_map = {t.name: t for t in schema.tables}

    # COMMENT ON TABLE
    for match in re.finditer(
        r"COMMENT\s+ON\s+TABLE\s+\"([^\"]+)\"\s+IS\s+'((?:[^']|'')*)'",
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
        r"COMMENT\s+ON\s+COLUMN\s+\"([^\"]+)\"\.\"([^\"]+)\"\s+IS\s+'((?:[^']|'')*)'",
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
        r'ALTER\s+TABLE\s+"([^"]+)"\s+ADD\s+CONSTRAINT\s+"([^"]+)"\s+'
        r'FOREIGN\s+KEY\s*\("([^"]+)"\)\s*REFERENCES\s+"([^"]+)"\s*\("([^"]+)"\)',
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
