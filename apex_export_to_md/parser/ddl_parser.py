# apex_export_to_md/parser/ddl_parser.py
"""Parser SQL DDL — ekstrakcja obiektów bazy z plików .sql.

Podejście regex-based. Podział na bloki z uwzględnieniem stringów
i bloków PL/SQL. Deduplikacja first-wins. Tolerancja błędów.
"""
from __future__ import annotations
import re
import logging
from pathlib import Path
from apex_export_to_md.models.db_models import (
    DbColumn, DbConstraint, DbIndex, DbTable, DbView,
    DbSequence, DbParameter, DbSubprogram, DbPackage, DbSchema,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Podział na bloki (statements)
# ---------------------------------------------------------------------------

def split_into_blocks(sql: str) -> list[str]:
    """Podziel SQL na bloki statement'ów.

    Bloki PL/SQL (PACKAGE) kończą się '/' na osobnej linii.
    Bloki DDL kończą się ';' poza stringami.
    Automat stanowy śledzi kontekst stringów (single-quoted literals).
    """
    blocks: list[str] = []

    # Krok 1: wydziel bloki PL/SQL (od create...package do / na osobnej linii)
    plsql_pattern = re.compile(
        r'(create\s+(?:or\s+replace\s+)?package\s+(?:body\s+)?.*?)\n\s*/\s*$',
        re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )
    remaining = sql
    plsql_blocks: list[str] = []
    for m in plsql_pattern.finditer(sql):
        plsql_blocks.append(m.group(1).strip())

    # Usuń bloki PL/SQL z remaining
    for plb in plsql_blocks:
        remaining = remaining.replace(plb, "", 1)
    # Usuń samotne '/' po usunięciu bloków PL/SQL
    remaining = re.sub(r'^\s*/\s*$', '', remaining, flags=re.MULTILINE)

    # Krok 2: podziel resztę na bloki po ';' (z uwzgl. stringów)
    ddl_blocks = _split_by_semicolon(remaining)

    # Złóż razem
    blocks = ddl_blocks + plsql_blocks

    # Filtruj puste bloki i samotne '/'
    return [b for b in blocks if b.strip() and b.strip() != '/']


def _split_by_semicolon(sql: str) -> list[str]:
    """Podziel SQL po ';' z uwzględnieniem stringów single-quoted."""
    blocks: list[str] = []
    current: list[str] = []
    in_quote = False
    i = 0
    chars = sql

    while i < len(chars):
        ch = chars[i]

        if ch == "'" and not in_quote:
            in_quote = True
            current.append(ch)
        elif ch == "'" and in_quote:
            # Sprawdź escape ''
            if i + 1 < len(chars) and chars[i + 1] == "'":
                current.append("''")
                i += 1  # pomiń następny apostrof
            else:
                in_quote = False
                current.append(ch)
        elif ch == ";" and not in_quote:
            block = "".join(current).strip()
            if block:
                blocks.append(block)
            current = []
        else:
            current.append(ch)

        i += 1

    # Ostatni blok (bez kończącego ';')
    last = "".join(current).strip()
    if last:
        blocks.append(last)

    return blocks


# ---------------------------------------------------------------------------
# Parsowanie CREATE TABLE
# ---------------------------------------------------------------------------

def parse_create_table(sql: str) -> DbTable | None:
    """Parsuj blok CREATE TABLE na obiekt DbTable."""
    m = re.match(r'CREATE\s+TABLE\s+"?(\w+)"?\s*\(', sql, re.IGNORECASE)
    if not m:
        return None

    table_name = m.group(1)
    body = _extract_table_body(sql, m.end() - 1)
    if not body:
        return None

    columns: list[DbColumn] = []
    constraints: list[DbConstraint] = []

    elements = _split_table_elements(body)

    for elem in elements:
        elem_stripped = elem.strip()
        if not elem_stripped:
            continue

        constraint = _parse_inline_constraint(elem_stripped)
        if constraint:
            constraints.append(constraint)
            continue

        if re.match(r'USING\s+INDEX', elem_stripped, re.IGNORECASE):
            continue

        col = _parse_column_def(elem_stripped)
        if col:
            columns.append(col)

    return DbTable(name=table_name, columns=columns, constraints=constraints)


def _extract_table_body(sql: str, paren_start: int) -> str | None:
    """Wyciągnij zawartość nawiasów z definicji CREATE TABLE."""
    depth = 0
    start = None
    for i in range(paren_start, len(sql)):
        if sql[i] == '(':
            if depth == 0:
                start = i + 1
            depth += 1
        elif sql[i] == ')':
            depth -= 1
            if depth == 0:
                return sql[start:i]
    return None


def _split_table_elements(body: str) -> list[str]:
    """Podziel body tabeli na elementy po ',' (top-level, nie w nawiasach).

    Obsługuje '' (escape Oracle) — podwójny apostrof nie zmienia stanu.
    """
    elements: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote = False
    i = 0

    while i < len(body):
        ch = body[i]

        if ch == "'" and not in_quote:
            in_quote = True
            current.append(ch)
        elif ch == "'" and in_quote:
            # Sprawdź escape ''
            if i + 1 < len(body) and body[i + 1] == "'":
                current.append("''")
                i += 1  # pomiń następny apostrof
            else:
                in_quote = False
                current.append(ch)
        elif ch == '(' and not in_quote:
            depth += 1
            current.append(ch)
        elif ch == ')' and not in_quote:
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0 and not in_quote:
            elements.append("".join(current))
            current = []
        else:
            current.append(ch)

        i += 1

    if current:
        elements.append("".join(current))

    return elements


def _parse_column_def(elem: str) -> DbColumn | None:
    """Parsuj definicję kolumny z elementu CREATE TABLE."""
    m = re.match(r'"?(\w+)"?\s+', elem)
    if not m:
        return None

    col_name = m.group(1)
    rest = elem[m.end():]

    data_type = _extract_data_type(rest)
    if not data_type:
        return None

    identity = bool(re.search(r'GENERATED\b.*?\bAS\s+IDENTITY\b', rest, re.IGNORECASE))
    nullable = not bool(re.search(r'\bNOT\s+NULL\b', rest, re.IGNORECASE))
    default = _extract_default(rest)

    return DbColumn(
        name=col_name,
        data_type=data_type,
        nullable=nullable,
        default=default,
        identity=identity,
    )


def _extract_data_type(rest: str) -> str | None:
    """Wyciągnij typ danych z reszty definicji kolumny."""
    m = re.match(r'((?:VARCHAR2|NUMBER|CHAR|NCHAR|NVARCHAR2|RAW|FLOAT)\s*\([^)]+\))', rest, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.match(r'(TIMESTAMP\s*\(\s*\d+\s*\))', rest, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.match(r'(CLOB|BLOB|DATE|NUMBER|TIMESTAMP|INTEGER|XMLTYPE)\b', rest, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    return None


def _extract_default(rest: str) -> str | None:
    """Wyciągnij wartość DEFAULT z reszty definicji kolumny.

    Obsługuje: DEFAULT 'Otwarty', DEFAULT SYSDATE, DEFAULT 0,
    DEFAULT "DAW"."SEQ"."NEXTVAL", DEFAULT SYSTIMESTAMP.
    Pomija DEFAULT ON NULL AS IDENTITY (to nie jest default użytkownika).
    """
    if re.search(r'GENERATED\b.*?\bAS\s+IDENTITY\b', rest, re.IGNORECASE):
        return None

    m = re.search(r'\bDEFAULT\s+', rest, re.IGNORECASE)
    if not m:
        return None

    after_default = rest[m.end():]
    # String literal (z obsługą '' escape)
    if after_default.startswith("'"):
        end = after_default.find("'", 1)
        while end > 0 and end + 1 < len(after_default) and after_default[end + 1] == "'":
            end = after_default.find("'", end + 2)
        if end > 0:
            return after_default[:end + 1]
        # Unterminated string — zwróć None
        return None

    # Quoted identifier: "DAW"."SEQ"."NEXTVAL"
    m2 = re.match(r'("[\w.]+"(?:\."[\w.]+")*)', after_default)
    if m2:
        return m2.group(1)

    # Proste wartości: SYSDATE, SYSTIMESTAMP, 0, NULL
    m2 = re.match(r'(\w+)', after_default)
    if m2:
        return m2.group(1)

    return None


def _parse_inline_constraint(elem: str) -> DbConstraint | None:
    """Parsuj inline constraint z elementu CREATE TABLE."""
    # CONSTRAINT "name" PRIMARY KEY ("col1", "col2")
    m = re.match(
        r'CONSTRAINT\s+"?(\w+)"?\s+PRIMARY\s+KEY\s*\(([^)]+)\)',
        elem, re.IGNORECASE,
    )
    if m:
        cols = _parse_column_list(m.group(2))
        return DbConstraint(name=m.group(1), constraint_type="PK", columns=cols)

    # CONSTRAINT "name" UNIQUE ("col1", "col2")
    m = re.match(
        r'CONSTRAINT\s+"?(\w+)"?\s+UNIQUE\s*\(([^)]+)\)',
        elem, re.IGNORECASE,
    )
    if m:
        cols = _parse_column_list(m.group(2))
        return DbConstraint(name=m.group(1), constraint_type="UQ", columns=cols)

    # CONSTRAINT "name" CHECK (expression)
    m = re.match(
        r'CONSTRAINT\s+"?(\w+)"?\s+CHECK\s*\((.+)\)',
        elem, re.IGNORECASE | re.DOTALL,
    )
    if m:
        expr = m.group(2).strip()
        expr = re.sub(r'\s+ENABLE\s*$', '', expr, flags=re.IGNORECASE)
        return DbConstraint(name=m.group(1), constraint_type="CHK", check_expression=expr)

    # PRIMARY KEY bez nazwy
    m = re.match(r'PRIMARY\s+KEY\s*\(([^)]+)\)', elem, re.IGNORECASE)
    if m:
        cols = _parse_column_list(m.group(1))
        return DbConstraint(name="", constraint_type="PK", columns=cols)

    return None


def _parse_column_list(s: str) -> list[str]:
    """Parsuj listę kolumn z nawiasu: ("A", "B") → ["A", "B"]."""
    return [c.strip().strip('"') for c in s.split(",") if c.strip()]


# ---------------------------------------------------------------------------
# Parsowanie ALTER TABLE (FK, UNIQUE)
# ---------------------------------------------------------------------------

def parse_alter_table_fk(sql: str) -> tuple[str, DbConstraint] | None:
    """Parsuj ALTER TABLE ... ADD CONSTRAINT (FK lub UNIQUE)."""
    # FK
    m = re.match(
        r'ALTER\s+TABLE\s+"?(\w+)"?\s+ADD\s+CONSTRAINT\s+"?(\w+)"?\s+'
        r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*'
        r'REFERENCES\s+"?(\w+)"?\s*\(([^)]+)\)',
        sql, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1), DbConstraint(
            name=m.group(2),
            constraint_type="FK",
            columns=_parse_column_list(m.group(3)),
            ref_table=m.group(4),
            ref_columns=_parse_column_list(m.group(5)),
        )

    # UNIQUE via ALTER TABLE
    m = re.match(
        r'ALTER\s+TABLE\s+"?(\w+)"?\s+ADD\s+CONSTRAINT\s+"?(\w+)"?\s+'
        r'UNIQUE\s*\(([^)]+)\)',
        sql, re.IGNORECASE,
    )
    if m:
        return m.group(1), DbConstraint(
            name=m.group(2),
            constraint_type="UQ",
            columns=_parse_column_list(m.group(3)),
        )

    return None


# ---------------------------------------------------------------------------
# Parsowanie CREATE INDEX
# ---------------------------------------------------------------------------

def parse_create_index(sql: str) -> DbIndex | None:
    """Parsuj CREATE [UNIQUE] INDEX."""
    m = re.match(
        r'CREATE\s+(UNIQUE\s+)?INDEX\s+"?(\w+)"?\s+ON\s+"?(\w+)"?\s*\(([^)]+)\)',
        sql, re.IGNORECASE,
    )
    if not m:
        logger.warning("Pominięto malformowany index: %s", sql[:80])
        return None

    return DbIndex(
        name=m.group(2),
        table_name=m.group(3),
        columns=_parse_column_list(m.group(4)),
        unique=bool(m.group(1)),
    )


# ---------------------------------------------------------------------------
# Parsowanie COMMENT ON
# ---------------------------------------------------------------------------

def parse_comment_on(sql: str) -> tuple[str, str, str | None, str] | None:
    """Parsuj COMMENT ON TABLE/COLUMN.

    Zwraca: (typ_obiektu, nazwa_obiektu, nazwa_kolumny|None, tekst_komentarza)
    Obsługuje '' (escape Oracle) wewnątrz tekstu komentarza.
    """
    # Wspólny helper: wyciągnij tekst między IS '...' (z uwzgl. '')
    def _extract_comment_text(s: str, start: int) -> str | None:
        """Wyciągnij tekst komentarza od pozycji start (po IS ')."""
        in_text = []
        i = start
        while i < len(s):
            ch = s[i]
            if ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    in_text.append("''")
                    i += 2
                    continue
                else:
                    return "".join(in_text)
            in_text.append(ch)
            i += 1
        return "".join(in_text) if in_text else None

    # COMMENT ON COLUMN "TABLE"."COLUMN" IS '...'
    m = re.match(
        r"COMMENT\s+ON\s+COLUMN\s+\"?(\w+)\"?\.\"?(\w+)\"?\s+IS\s+'",
        sql, re.IGNORECASE,
    )
    if m:
        text = _extract_comment_text(sql, m.end())
        if text is not None:
            return ("COLUMN", m.group(1), m.group(2), text)

    # COMMENT ON TABLE "TABLE" IS '...'
    m = re.match(
        r"COMMENT\s+ON\s+TABLE\s+\"?(\w+)\"?\s+IS\s+'",
        sql, re.IGNORECASE,
    )
    if m:
        text = _extract_comment_text(sql, m.end())
        if text is not None:
            return ("TABLE", m.group(1), None, text)

    return None


# ---------------------------------------------------------------------------
# Parsowanie CREATE SEQUENCE
# ---------------------------------------------------------------------------

def parse_create_sequence(sql: str) -> DbSequence | None:
    """Parsuj CREATE SEQUENCE."""
    m = re.match(r'CREATE\s+SEQUENCE\s+"?(\w+)"?', sql, re.IGNORECASE)
    if not m:
        return None

    name = m.group(1)

    def _extract(pattern: str) -> str | None:
        m2 = re.search(pattern, sql, re.IGNORECASE)
        return m2.group(1) if m2 else None

    return DbSequence(
        name=name,
        min_value=_extract(r'MINVALUE\s+(\d+)'),
        max_value=_extract(r'MAXVALUE\s+(\d+)'),
        increment_by=_extract(r'INCREMENT\s+BY\s+(\d+)'),
        start_with=_extract(r'START\s+WITH\s+(\d+)'),
        cache=_extract(r'CACHE\s+(\d+)'),
        nocache=bool(re.search(r'\bNOCACHE\b', sql, re.IGNORECASE)),
    )


# ---------------------------------------------------------------------------
# Parsowanie CREATE VIEW
# ---------------------------------------------------------------------------

def parse_create_view(sql: str) -> DbView | None:
    """Parsuj CREATE [OR REPLACE] [FORCE] [EDITIONABLE] VIEW."""
    m = re.match(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?(?:EDITIONABLE\s+)?VIEW\s+"?(\w+)"?',
        sql, re.IGNORECASE,
    )
    if not m:
        return None

    name = m.group(1)
    rest = sql[m.end():]
    columns: list[str] = []
    col_match = re.match(r'\s*\(([^)]+)\)\s+AS\b', rest, re.IGNORECASE)
    if col_match:
        columns = _parse_column_list(col_match.group(1))
        rest = rest[col_match.end():]
    else:
        as_match = re.match(r'\s+AS\b', rest, re.IGNORECASE)
        if as_match:
            rest = rest[as_match.end():]

    view_sql = rest.strip().rstrip(';').strip()
    return DbView(name=name, columns=columns, sql=view_sql)


# ---------------------------------------------------------------------------
# Parsowanie PACKAGE (spec i body)
# ---------------------------------------------------------------------------

def _extract_error_codes(source: str) -> list[tuple[int, str]]:
    """Wyciągnij kody błędów z RAISE_APPLICATION_ERROR w kodzie PL/SQL.

    Zwraca listę (kod, tekst) posortowaną po kodzie.
    Tekst = pierwszy string literal po kodzie (przed || jeśli jest konkatenacja).
    """
    codes: list[tuple[int, str]] = []
    for m in re.finditer(
        r"RAISE_APPLICATION_ERROR\(\s*(-\d+)\s*,\s*'([^']*)'",
        source, re.IGNORECASE,
    ):
        code = int(m.group(1))
        text = m.group(2)
        codes.append((code, text))
    # Deduplikacja po kodzie, zachowaj pierwszy
    seen: set[int] = set()
    unique: list[tuple[int, str]] = []
    for code, text in codes:
        if code not in seen:
            seen.add(code)
            unique.append((code, text))
    return sorted(unique, key=lambda x: x[0], reverse=True)


def parse_package(sql: str) -> DbPackage | None:
    """Parsuj PACKAGE spec lub PACKAGE BODY."""
    m = re.match(
        r'create\s+(?:or\s+replace\s+)?PACKAGE\s+(BODY\s+)?"?(\w+)"?\s+(?:AS|IS)\b',
        sql, re.IGNORECASE,
    )
    if not m:
        return None

    is_body = bool(m.group(1))
    name = m.group(2)
    source = sql.strip()

    constants: list[str] = []
    for cm in re.finditer(
        r'(\w+\s+CONSTANT\s+\w+.*?:=\s*[^;]+)',
        source, re.IGNORECASE,
    ):
        constants.append(cm.group(1).strip())

    subprograms = _extract_subprograms(source)

    pkg = DbPackage(name=name, constants=constants)
    if is_body:
        pkg.body_subprograms = subprograms
        pkg.body_source = source
        pkg.error_codes = _extract_error_codes(source)
    else:
        pkg.spec_subprograms = subprograms
        pkg.spec_source = source

    return pkg


def _extract_subprograms(source: str) -> list[DbSubprogram]:
    """Wyciągnij procedury i funkcje z kodu pakietu."""
    subprograms: list[DbSubprogram] = []
    lines = source.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r'(?:PROCEDURE|FUNCTION)\s+(\w+)', stripped, re.IGNORECASE)
        if not m:
            continue

        sub_name = m.group(1)
        is_func = stripped.upper().startswith('FUNCTION')
        description = _collect_description_above(lines, i)
        params_text = _collect_params_text(lines, i)
        parameters = _parse_parameters(params_text) if params_text else []

        return_type = None
        if is_func:
            for j in range(i, min(i + 20, len(lines))):
                rm = re.search(r'\)\s*RETURN\s+(\w+)', lines[j], re.IGNORECASE)
                if rm:
                    return_type = rm.group(1)
                    break
                rm = re.search(r'RETURN\s+(\w+)\s*[;IS]', lines[j], re.IGNORECASE)
                if rm and j > i:
                    return_type = rm.group(1)
                    break

        subprograms.append(DbSubprogram(
            name=sub_name,
            subprogram_type="FUNCTION" if is_func else "PROCEDURE",
            parameters=parameters,
            return_type=return_type,
            description=description,
        ))

    return subprograms


def _collect_description_above(lines: list[str], idx: int) -> str | None:
    """Zbierz opis z komentarzy '--' bezpośrednio nad procedurą/funkcją."""
    desc_lines: list[str] = []
    for j in range(idx - 1, -1, -1):
        stripped = lines[j].strip()
        if stripped.startswith('--'):
            text = stripped.lstrip('-').strip()
            if text and not re.match(r'^[=\-]+$', text):
                desc_lines.insert(0, text)
        elif stripped == '':
            continue
        else:
            break
    return " ".join(desc_lines) if desc_lines else None


def _collect_params_text(lines: list[str], start_idx: int) -> str:
    """Zbierz tekst parametrów procedury/funkcji (od '(' do ')')."""
    text_lines = []
    collecting = False
    depth = 0

    for j in range(start_idx, min(start_idx + 30, len(lines))):
        line = lines[j]
        for ch in line:
            if ch == '(':
                if not collecting:
                    collecting = True
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return "".join(text_lines)
            if collecting and depth > 0:
                text_lines.append(ch)
        if collecting:
            text_lines.append(' ')

    return "".join(text_lines)


def _parse_parameters(params_text: str) -> list[DbParameter]:
    """Parsuj listę parametrów z tekstu: p_name IN VARCHAR2, p_id OUT NUMBER."""
    cleaned = params_text.strip().lstrip('(').strip()
    if not cleaned:
        return []

    params: list[DbParameter] = []
    parts = [p.strip() for p in cleaned.split(',') if p.strip()]

    for part in parts:
        part = re.sub(r'--.*$', '', part, flags=re.MULTILINE).strip()
        m = re.match(r'(\w+)\s+(IN\s+OUT|OUT|IN)?\s*(\w+)', part, re.IGNORECASE)
        if m:
            direction = (m.group(2) or "IN").strip().upper()
            params.append(DbParameter(
                name=m.group(1),
                data_type=m.group(3),
                direction=direction,
            ))

    return params


# ---------------------------------------------------------------------------
# Orchestrator — parse_ddl i parse_ddl_files
# ---------------------------------------------------------------------------

def parse_ddl(sql: str) -> DbSchema:
    """Parsuj pełny plik SQL DDL i zwróć DbSchema.

    Pipeline: split → classify → extract → dedup → merge packages → assign comments.
    """
    blocks = split_into_blocks(sql)

    tables: dict[str, DbTable] = {}
    fk_constraints: list[tuple[str, DbConstraint]] = []
    indexes: dict[str, DbIndex] = {}
    table_comments: dict[str, str] = {}
    column_comments: dict[str, dict[str, str]] = {}
    views: dict[str, DbView] = {}
    sequences: dict[str, DbSequence] = {}
    packages: dict[str, DbPackage] = {}

    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue

        upper = stripped.upper().lstrip()

        try:
            if upper.startswith("CREATE TABLE"):
                table = parse_create_table(stripped)
                if table and table.name not in tables:
                    tables[table.name] = table

            elif upper.startswith("ALTER TABLE"):
                result = parse_alter_table_fk(stripped)
                if result:
                    fk_constraints.append(result)

            elif "PACKAGE" in upper and upper.startswith("CREATE"):
                # PACKAGE musi być przed INDEX/VIEW — body PL/SQL
                # może zawierać słowa INDEX/VIEW w kodzie
                pkg = parse_package(stripped)
                if pkg:
                    if pkg.name in packages:
                        existing = packages[pkg.name]
                        if pkg.spec_source:
                            existing.spec_subprograms = pkg.spec_subprograms
                            existing.spec_source = pkg.spec_source
                        if pkg.body_source:
                            existing.body_subprograms = pkg.body_subprograms
                            existing.body_source = pkg.body_source
                        if pkg.constants:
                            existing.constants = existing.constants or pkg.constants
                    else:
                        packages[pkg.name] = pkg

            elif "INDEX" in upper and upper.startswith("CREATE"):
                idx = parse_create_index(stripped)
                if idx and idx.name not in indexes:
                    indexes[idx.name] = idx

            elif upper.startswith("COMMENT ON"):
                result = parse_comment_on(stripped)
                if result:
                    obj_type, obj_name, col_name, text = result
                    if obj_type == "TABLE":
                        if obj_name not in table_comments:
                            table_comments[obj_name] = text
                    elif obj_type == "COLUMN":
                        if obj_name not in column_comments:
                            column_comments[obj_name] = {}
                        if col_name not in column_comments[obj_name]:
                            column_comments[obj_name][col_name] = text

            elif upper.startswith("CREATE SEQUENCE"):
                seq = parse_create_sequence(stripped)
                if seq and seq.name not in sequences:
                    sequences[seq.name] = seq

            elif "VIEW" in upper and upper.startswith("CREATE"):
                view = parse_create_view(stripped)
                if view and view.name not in views:
                    views[view.name] = view

        except Exception as e:
            logger.warning("Błąd parsowania bloku: %s — %s", stripped[:60], e)

    # --- Post-processing ---

    # Przypisz FK constraints do tabel
    for table_name, constraint in fk_constraints:
        if table_name in tables:
            existing_names = {c.name for c in tables[table_name].constraints}
            if constraint.name not in existing_names:
                tables[table_name].constraints.append(constraint)

    # Przypisz indeksy do tabel
    for idx in indexes.values():
        if idx.table_name in tables:
            tables[idx.table_name].indexes.append(idx)

    # Przypisz komentarze tabel/widoków
    for obj_name, comment in table_comments.items():
        if obj_name in views:
            views[obj_name].comment = comment
        elif obj_name in tables:
            tables[obj_name].comment = comment

    # Przypisz komentarze kolumn
    for table_name, cols in column_comments.items():
        if table_name in tables:
            for col in tables[table_name].columns:
                if col.name in cols:
                    col.comment = cols[col.name]

    # Ustaw visibility prywatnych subprogramów w body
    for pkg in packages.values():
        spec_names = {s.name for s in pkg.spec_subprograms}
        for sub in pkg.body_subprograms:
            if sub.name not in spec_names:
                sub.visibility = "private"

    return DbSchema(
        tables=list(tables.values()),
        views=list(views.values()),
        packages=list(packages.values()),
        sequences=list(sequences.values()),
    )


def parse_ddl_files(files: list[Path]) -> DbSchema:
    """Parsuj wiele plików SQL i połącz w jeden DbSchema."""
    combined_sql_parts: list[str] = []
    for f in files:
        path = Path(f)
        try:
            content = path.read_text(encoding="utf-8")
            combined_sql_parts.append(content)
            logger.info("Wczytano plik SQL: %s (%d znaków)", path.name, len(content))
        except Exception as e:
            logger.warning("Nie udało się wczytać pliku %s: %s", path, e)

    combined_sql = "\n\n".join(combined_sql_parts)
    return parse_ddl(combined_sql)
