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
        r'(create\s+(?:or\s+replace\s+)?(?:PACKAGE|package)\s+(?:BODY\s+|body\s+)?.*?)\n\s*/\s*$',
        re.DOTALL | re.MULTILINE,
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
    )
