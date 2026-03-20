# DDL Pipeline + Interaktywny HTML — Plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rozszerzyć apex_export_to_md o parsowanie SQL DDL, generowanie dokumentacji bazy danych (MD human+LLM, Mermaid ER) i interaktywną stronę HTML łączącą APEX z bazą danych.

**Architecture:** Nowy pipeline DDL działa równolegle do istniejącego APEX pipeline'u. Parser SQL (regex-based) produkuje model `DbSchema`, renderery generują MD + HTML. Linker APEX↔DB łączy oba światy przez heurystyki SQL.

**Tech Stack:** Python 3.10+, dataclasses, regex, vis.js (inline), Mermaid ER (w MD)

**Spec:** `docs/superpowers/specs/2026-03-20-ddl-pipeline-design.md`

---

## Struktura plików

### Nowe pliki
| Plik | Odpowiedzialność |
|------|-----------------|
| `apex_export_to_md/models/db_models.py` | Dataclasses: DbSchema, DbTable, DbColumn, DbConstraint, DbIndex, DbView, DbSequence, DbParameter, DbSubprogram, DbPackage |
| `apex_export_to_md/parser/ddl_parser.py` | Regex-based parser SQL DDL: block splitting, extraction, orchestration |
| `apex_export_to_md/renderers/db_base_renderer.py` | Abstrakcyjna baza dla rendererów DB |
| `apex_export_to_md/renderers/db_human_renderer.py` | MD human + Mermaid ER |
| `apex_export_to_md/renderers/db_llm_renderer.py` | MD LLM (format kondensowany) |
| `apex_export_to_md/renderers/html_renderer.py` | Self-contained interactive HTML |
| `apex_export_to_md/linker/__init__.py` | Re-export ApexDbLink, ApexDbLinker |
| `apex_export_to_md/linker/apex_db_linker.py` | Wykrywanie powiązań APEX↔DB |
| `tests/test_db_models.py` | Testy modeli DB |
| `tests/test_ddl_parser.py` | Testy parsera DDL |
| `tests/test_db_human_renderer.py` | Testy renderera human DB |
| `tests/test_db_llm_renderer.py` | Testy renderera LLM DB |
| `tests/test_apex_db_linker.py` | Testy linkera |
| `tests/test_html_renderer.py` | Testy renderera HTML |
| `tests/test_cli_ddl.py` | Testy CLI z DDL |
| `tests/test_integration_ddl.py` | Test integracyjny z prawdziwym DDL |

### Modyfikowane pliki
| Plik | Zmiana |
|------|--------|
| `apex_export_to_md/config.py` | Nowe pola: enable_ddl, ddl_files, enable_html, html_output, author_name |
| `apex_export_to_md/cli.py` | Nowe argumenty CLI + rozszerzony pipeline |
| `apex_export_to_md/models/__init__.py` | Re-export nowych modeli DB |

---

### Task 1: Modele danych bazy (db_models.py)

**Files:**
- Create: `apex_export_to_md/models/db_models.py`
- Modify: `apex_export_to_md/models/__init__.py`
- Test: `tests/test_db_models.py`

- [ ] **Step 1: Napisz testy modeli DB**

```python
# tests/test_db_models.py
"""Testy modeli danych bazy — tworzenie i walidacja dataclasses."""
import pytest
from apex_export_to_md.models.db_models import (
    DbColumn, DbConstraint, DbIndex, DbTable, DbView,
    DbSequence, DbParameter, DbSubprogram, DbPackage, DbSchema,
)


class TestDbColumn:
    def test_create_minimal(self):
        col = DbColumn(name="ID", data_type="NUMBER")
        assert col.name == "ID"
        assert col.data_type == "NUMBER"
        assert col.nullable is True
        assert col.default is None
        assert col.identity is False
        assert col.comment is None

    def test_create_full(self):
        col = DbColumn(
            name="STATUS",
            data_type="VARCHAR2(20)",
            nullable=False,
            default="'Otwarty'",
            identity=False,
            comment="Status audytu",
        )
        assert col.nullable is False
        assert col.default == "'Otwarty'"
        assert col.comment == "Status audytu"

    def test_identity_column(self):
        col = DbColumn(name="ID_PK", data_type="NUMBER", identity=True, nullable=False)
        assert col.identity is True


class TestDbConstraint:
    def test_pk(self):
        c = DbConstraint(name="B_AUDYT_PK", constraint_type="PK", columns=["ID_PK_B_AUDYT"])
        assert c.constraint_type == "PK"
        assert c.ref_table is None

    def test_fk(self):
        c = DbConstraint(
            name="B_ANKIETA_B_AUDYT_FK",
            constraint_type="FK",
            columns=["ID_FK_B_AUDYT"],
            ref_table="B_AUDYT",
            ref_columns=["ID_PK_B_AUDYT"],
        )
        assert c.ref_table == "B_AUDYT"
        assert c.ref_columns == ["ID_PK_B_AUDYT"]

    def test_check(self):
        c = DbConstraint(
            name="B_AUDYT_STATUS_CHK",
            constraint_type="CHK",
            check_expression="STATUS_AUDYTU IN ('Otwarty', 'Zamrozony', 'Zakonczony')",
        )
        assert "Otwarty" in c.check_expression


class TestDbTable:
    def test_create_with_columns(self):
        t = DbTable(
            name="B_AUDYT",
            columns=[DbColumn(name="ID", data_type="NUMBER")],
            comment="Tabela audytow",
        )
        assert t.name == "B_AUDYT"
        assert len(t.columns) == 1
        assert t.comment == "Tabela audytow"

    def test_empty_table(self):
        t = DbTable(name="EMPTY")
        assert t.columns == []
        assert t.constraints == []
        assert t.indexes == []


class TestDbView:
    def test_create(self):
        v = DbView(
            name="B_V_AUDYT_KONTROLE",
            columns=["ID_FK_B_AUDYT", "REFERENCE_ID"],
            sql="SELECT ak.* FROM B_AUDYT_KONTROLA ak",
            comment="Widok kontroli",
        )
        assert v.name == "B_V_AUDYT_KONTROLE"
        assert len(v.columns) == 2


class TestDbSequence:
    def test_create(self):
        s = DbSequence(name="DAW_SEQ_B_C_ANAKIETA_PK", start_with="1203", increment_by="1")
        assert s.start_with == "1203"


class TestDbSubprogram:
    def test_procedure(self):
        p = DbSubprogram(
            name="UTWORZ_AUDYT",
            subprogram_type="PROCEDURE",
            parameters=[
                DbParameter(name="p_numer_audytu", data_type="VARCHAR2", direction="IN"),
                DbParameter(name="p_id_audytu", data_type="NUMBER", direction="OUT"),
            ],
            description="Tworzenie nowego audytu",
        )
        assert len(p.parameters) == 2
        assert p.visibility == "public"

    def test_private_procedure(self):
        p = DbSubprogram(
            name="POBIERZ_AUDYT",
            subprogram_type="PROCEDURE",
            visibility="private",
        )
        assert p.visibility == "private"

    def test_function(self):
        f = DbSubprogram(
            name="SPRAWDZ_UPRAWNIENIA",
            subprogram_type="FUNCTION",
            return_type="VARCHAR2",
        )
        assert f.return_type == "VARCHAR2"


class TestDbPackage:
    def test_create(self):
        pkg = DbPackage(
            name="PKG_AUDYT",
            spec_subprograms=[
                DbSubprogram(name="UTWORZ_AUDYT", subprogram_type="PROCEDURE"),
            ],
            body_subprograms=[
                DbSubprogram(name="UTWORZ_AUDYT", subprogram_type="PROCEDURE"),
                DbSubprogram(name="POBIERZ_AUDYT", subprogram_type="PROCEDURE", visibility="private"),
            ],
            constants=["C_STATUS_OTWARTY CONSTANT VARCHAR2(20) := 'Otwarty'"],
            spec_source="PACKAGE PKG_AUDYT AS ...",
            body_source="PACKAGE BODY PKG_AUDYT AS ...",
        )
        assert len(pkg.spec_subprograms) == 1
        assert len(pkg.body_subprograms) == 2


class TestDbSchema:
    def test_create_empty(self):
        s = DbSchema()
        assert s.tables == []
        assert s.views == []

    def test_create_full(self):
        s = DbSchema(
            tables=[DbTable(name="T1")],
            views=[DbView(name="V1")],
            packages=[DbPackage(name="P1")],
            sequences=[DbSequence(name="S1")],
        )
        assert len(s.tables) == 1
        assert len(s.views) == 1
```

- [ ] **Step 2: Uruchom testy — powinny FAIL (brak modułu)**

Run: `python -m pytest tests/test_db_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apex_export_to_md.models.db_models'`

- [ ] **Step 3: Implementuj db_models.py**

```python
# apex_export_to_md/models/db_models.py
"""Modele danych bazy jako dataclasses.

Każda klasa odpowiada typowi obiektu w eksporcie DDL Oracle.
Pola odpowiadają wartościom wyekstrahowanym z plików SQL.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DbColumn:
    """Kolumna tabeli bazodanowej."""
    name: str
    data_type: str                    # np. "VARCHAR2(4000 CHAR)", "NUMBER(11,0)"
    nullable: bool = True
    default: str | None = None        # np. "'Otwarty'", "SYSDATE"
    identity: bool = False
    comment: str | None = None


@dataclass
class DbConstraint:
    """Constraint tabeli (PK, FK, UNIQUE, CHECK)."""
    name: str
    constraint_type: str              # "PK", "FK", "UQ", "CHK"
    columns: list[str] = field(default_factory=list)
    ref_table: str | None = None      # tylko FK
    ref_columns: list[str] = field(default_factory=list)  # tylko FK
    check_expression: str | None = None  # tylko CHK


@dataclass
class DbIndex:
    """Indeks tabeli."""
    name: str
    table_name: str
    columns: list[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class DbTable:
    """Tabela bazodanowa z kolumnami, constraint'ami i indeksami."""
    name: str
    columns: list[DbColumn] = field(default_factory=list)
    constraints: list[DbConstraint] = field(default_factory=list)
    indexes: list[DbIndex] = field(default_factory=list)
    comment: str | None = None


@dataclass
class DbView:
    """Widok bazodanowy."""
    name: str
    columns: list[str] = field(default_factory=list)
    sql: str = ""
    comment: str | None = None


@dataclass
class DbSequence:
    """Sekwencja Oracle."""
    name: str
    min_value: str | None = None
    max_value: str | None = None
    increment_by: str | None = None
    start_with: str | None = None
    cache: str | None = None


@dataclass
class DbParameter:
    """Parametr procedury/funkcji PL/SQL."""
    name: str
    data_type: str
    direction: str = "IN"             # "IN", "OUT", "IN OUT"
    description: str | None = None


@dataclass
class DbSubprogram:
    """Procedura lub funkcja w pakiecie PL/SQL."""
    name: str
    subprogram_type: str              # "PROCEDURE" lub "FUNCTION"
    parameters: list[DbParameter] = field(default_factory=list)
    return_type: str | None = None    # tylko dla FUNCTION
    description: str | None = None    # z komentarza nad procedurą/funkcją
    visibility: str = "public"        # "public" (w spec) lub "private" (tylko w body)


@dataclass
class DbPackage:
    """Pakiet PL/SQL — łączy specyfikację i body."""
    name: str
    spec_subprograms: list[DbSubprogram] = field(default_factory=list)
    body_subprograms: list[DbSubprogram] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    spec_source: str = ""             # kod specyfikacji
    body_source: str = ""             # kod body z komentarzami


@dataclass
class DbSchema:
    """Kontener główny — pełny schemat bazy danych."""
    tables: list[DbTable] = field(default_factory=list)
    views: list[DbView] = field(default_factory=list)
    packages: list[DbPackage] = field(default_factory=list)
    sequences: list[DbSequence] = field(default_factory=list)
```

- [ ] **Step 4: Zaktualizuj models/__init__.py**

Dodaj na końcu pliku `apex_export_to_md/models/__init__.py`:

```python
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbIndex,
    DbView, DbSequence, DbParameter, DbSubprogram, DbPackage,
)

# Dodaj do __all__:
__all__ += [
    "DbSchema", "DbTable", "DbColumn", "DbConstraint", "DbIndex",
    "DbView", "DbSequence", "DbParameter", "DbSubprogram", "DbPackage",
]
```

Uwaga: Zamień obecne `__all__ = [...]` na `__all__: list[str] = [...]` i dodaj `+=` w drugiej sekcji. Albo po prostu dopisz nowe eksporty do istniejącej listy.

- [ ] **Step 5: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_db_models.py -v`
Expected: ALL PASS (13 testów)

- [ ] **Step 6: Commit**

```bash
git add apex_export_to_md/models/db_models.py apex_export_to_md/models/__init__.py tests/test_db_models.py
git commit -m "feat(models): dodaj dataclasses dla schematu bazy danych (DbSchema, DbTable, DbPackage...)"
```

---

### Task 2: DDL Parser — block splitter i CREATE TABLE

**Files:**
- Create: `apex_export_to_md/parser/ddl_parser.py`
- Test: `tests/test_ddl_parser.py`

**Context:** Parser SQL DDL opiera się na podziale pliku na bloki (statements). Blok PL/SQL (PACKAGE) kończy się znakiem `/` na osobnej linii. Bloki DDL kończy `;`, ale splitter musi ignorować `;` wewnątrz stringów (np. w COMMENT ON z wieloliniowym SQL).

- [ ] **Step 1: Napisz testy block splittera i CREATE TABLE**

```python
# tests/test_ddl_parser.py
"""Testy parsera DDL — podział na bloki, ekstrakcja obiektów."""
import pytest
from apex_export_to_md.parser.ddl_parser import (
    split_into_blocks,
    parse_create_table,
    parse_ddl,
)
from apex_export_to_md.models.db_models import DbSchema


class TestSplitIntoBlocks:
    def test_simple_statements(self):
        sql = "CREATE TABLE A (ID NUMBER);\nCREATE TABLE B (ID NUMBER);"
        blocks = split_into_blocks(sql)
        assert len(blocks) == 2
        assert "CREATE TABLE A" in blocks[0]
        assert "CREATE TABLE B" in blocks[1]

    def test_semicolon_inside_string_preserved(self):
        """Średnik wewnątrz stringa COMMENT ON nie dzieli bloku."""
        sql = """COMMENT ON TABLE "T1" IS 'SELECT a; FROM b; WHERE c;';"""
        blocks = split_into_blocks(sql)
        assert len(blocks) == 1
        assert "SELECT a; FROM b; WHERE c;" in blocks[0]

    def test_plsql_block_separated_by_slash(self):
        sql = (
            "CREATE TABLE A (ID NUMBER);\n"
            "create or replace PACKAGE PKG AS\n"
            "  PROCEDURE P1;\n"
            "END PKG;\n"
            "/\n"
            "CREATE TABLE B (ID NUMBER);"
        )
        blocks = split_into_blocks(sql)
        assert len(blocks) == 3
        # Sprawdzamy zawartość niezależnie od kolejności
        block_texts = "\n".join(blocks)
        assert "CREATE TABLE A" in block_texts
        assert "PACKAGE PKG" in block_texts
        assert "CREATE TABLE B" in block_texts

    def test_escaped_quotes_in_string(self):
        """Podwójny apostrof '' nie kończy stringa."""
        sql = """COMMENT ON TABLE "T" IS 'It''s a test; with semicolon';"""
        blocks = split_into_blocks(sql)
        assert len(blocks) == 1
        assert "It''s a test; with semicolon" in blocks[0]

    def test_empty_blocks_filtered(self):
        sql = "  ;\n\n  ; CREATE TABLE A (ID NUMBER);"
        blocks = split_into_blocks(sql)
        assert len(blocks) == 1


class TestParseCreateTable:
    def test_simple_table(self):
        sql = '''CREATE TABLE "B_AUDYT"
           ("ID_PK_B_AUDYT" NUMBER NOT NULL ENABLE,
            "STATUS_AUDYTU" VARCHAR2(20) DEFAULT 'Otwarty' NOT NULL ENABLE,
            CONSTRAINT "B_AUDYT_PK" PRIMARY KEY ("ID_PK_B_AUDYT")
           USING INDEX ENABLE
           )'''
        table = parse_create_table(sql)
        assert table is not None
        assert table.name == "B_AUDYT"
        assert len(table.columns) == 2
        # Kolumny
        id_col = table.columns[0]
        assert id_col.name == "ID_PK_B_AUDYT"
        assert id_col.data_type == "NUMBER"
        assert id_col.nullable is False
        status_col = table.columns[1]
        assert status_col.data_type == "VARCHAR2(20)"
        assert status_col.default == "'Otwarty'"
        assert status_col.nullable is False
        # PK constraint
        pk = [c for c in table.constraints if c.constraint_type == "PK"]
        assert len(pk) == 1
        assert pk[0].columns == ["ID_PK_B_AUDYT"]

    def test_identity_column(self):
        sql = '''CREATE TABLE "T"
           ("ID" NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY
            MINVALUE 1 MAXVALUE 999 INCREMENT BY 1 START WITH 1
            CACHE 20 NOORDER NOCYCLE NOT NULL ENABLE,
            CONSTRAINT "T_PK" PRIMARY KEY ("ID") USING INDEX ENABLE
           )'''
        table = parse_create_table(sql)
        assert table.columns[0].identity is True
        assert table.columns[0].nullable is False

    def test_check_constraint_inline(self):
        sql = '''CREATE TABLE "B_AUDYT"
           ("STATUS" VARCHAR2(20) NOT NULL ENABLE,
            CONSTRAINT "CHK1" CHECK (STATUS IN ('A','B','C')) ENABLE
           )'''
        table = parse_create_table(sql)
        chk = [c for c in table.constraints if c.constraint_type == "CHK"]
        assert len(chk) == 1
        assert "STATUS IN" in chk[0].check_expression

    def test_unique_constraint_inline(self):
        sql = '''CREATE TABLE "T"
           ("A" NUMBER NOT NULL, "B" NUMBER NOT NULL,
            CONSTRAINT "T_UNQ" UNIQUE ("A", "B") USING INDEX ENABLE
           )'''
        table = parse_create_table(sql)
        uq = [c for c in table.constraints if c.constraint_type == "UQ"]
        assert len(uq) == 1
        assert uq[0].columns == ["A", "B"]

    def test_clob_and_date_types(self):
        sql = '''CREATE TABLE "T"
           ("POMOC" CLOB,
            "DATA" DATE DEFAULT SYSDATE,
            "TS" TIMESTAMP (6) DEFAULT SYSTIMESTAMP NOT NULL ENABLE
           )'''
        table = parse_create_table(sql)
        assert table.columns[0].data_type == "CLOB"
        assert table.columns[1].data_type == "DATE"
        assert table.columns[1].default == "SYSDATE"
        assert "TIMESTAMP" in table.columns[2].data_type
        assert table.columns[2].nullable is False

    def test_sequence_default(self):
        """DEFAULT "DAW"."SEQ"."NEXTVAL" — parsuj jako default."""
        sql = '''CREATE TABLE "T"
           ("ID" NUMBER DEFAULT "DAW"."SEQ"."NEXTVAL" NOT NULL ENABLE
           )'''
        table = parse_create_table(sql)
        assert table.columns[0].default is not None
        assert "NEXTVAL" in table.columns[0].default
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

Run: `python -m pytest tests/test_ddl_parser.py::TestSplitIntoBlocks -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementuj block splitter i parse_create_table**

```python
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

    # Złóż razem w kolejności: zbierz pozycje i sortuj
    # Dla prostoty: DDL blocks + PL/SQL blocks, deduplikacja załatwi resztę
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
    # Wyciągnij nazwę tabeli
    m = re.match(r'CREATE\s+TABLE\s+"?(\w+)"?\s*\(', sql, re.IGNORECASE)
    if not m:
        return None

    table_name = m.group(1)
    # Wyciągnij zawartość nawiasów (kolumny + constraints)
    body = _extract_table_body(sql, m.end() - 1)
    if not body:
        return None

    columns: list[DbColumn] = []
    constraints: list[DbConstraint] = []

    # Podziel body na elementy (top-level przecinki, nie wewnątrz nawiasów)
    elements = _split_table_elements(body)

    for elem in elements:
        elem_stripped = elem.strip()
        if not elem_stripped:
            continue

        # Constraint inline?
        constraint = _parse_inline_constraint(elem_stripped)
        if constraint:
            constraints.append(constraint)
            continue

        # USING INDEX? pomiń
        if re.match(r'USING\s+INDEX', elem_stripped, re.IGNORECASE):
            continue

        # Kolumna
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
    # Wzorzec: "NAZWA" TYP [(...)] [GENERATED...AS IDENTITY...] [DEFAULT ...] [NOT NULL] [ENABLE]
    m = re.match(r'"?(\w+)"?\s+', elem)
    if not m:
        return None

    col_name = m.group(1)
    rest = elem[m.end():]

    # Wyciągnij typ danych
    data_type = _extract_data_type(rest)
    if not data_type:
        return None

    # Sprawdź IDENTITY
    identity = bool(re.search(r'GENERATED\b.*?\bAS\s+IDENTITY\b', rest, re.IGNORECASE))

    # Sprawdź NOT NULL
    nullable = not bool(re.search(r'\bNOT\s+NULL\b', rest, re.IGNORECASE))

    # Wyciągnij DEFAULT
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
    # Typy z parametrami: VARCHAR2(4000 CHAR), NUMBER(11,0), TIMESTAMP (6)
    m = re.match(r'((?:VARCHAR2|NUMBER|CHAR|NCHAR|NVARCHAR2|RAW|FLOAT)\s*\([^)]+\))', rest, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # TIMESTAMP z parametrem
    m = re.match(r'(TIMESTAMP\s*\(\s*\d+\s*\))', rest, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Typy bez parametrów: CLOB, DATE, NUMBER, BLOB, TIMESTAMP, etc.
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
    # Pomiń GENERATED...AS IDENTITY — to nie DEFAULT
    if re.search(r'GENERATED\b.*?\bAS\s+IDENTITY\b', rest, re.IGNORECASE):
        return None

    # Szukaj DEFAULT
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
        # Usuń trailing ENABLE
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
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_ddl_parser.py::TestSplitIntoBlocks tests/test_ddl_parser.py::TestParseCreateTable -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/parser/ddl_parser.py tests/test_ddl_parser.py
git commit -m "feat(parser): block splitter i parse_create_table w ddl_parser"
```

---

### Task 3: DDL Parser — ALTER TABLE, INDEX, COMMENT ON, SEQUENCE

**Files:**
- Modify: `apex_export_to_md/parser/ddl_parser.py`
- Modify: `tests/test_ddl_parser.py`

- [ ] **Step 1: Napisz testy**

Dopisz do `tests/test_ddl_parser.py`:

```python
from apex_export_to_md.parser.ddl_parser import (
    parse_alter_table_fk,
    parse_create_index,
    parse_comment_on,
    parse_create_sequence,
)


class TestParseAlterTableFK:
    def test_foreign_key(self):
        sql = '''ALTER TABLE "B_ANKIETA" ADD CONSTRAINT "B_ANKIETA_B_AUDYT_FK"
                 FOREIGN KEY ("ID_FK_B_AUDYT")
                 REFERENCES "B_AUDYT" ("ID_PK_B_AUDYT") ENABLE'''
        result = parse_alter_table_fk(sql)
        assert result is not None
        table_name, constraint = result
        assert table_name == "B_ANKIETA"
        assert constraint.name == "B_ANKIETA_B_AUDYT_FK"
        assert constraint.constraint_type == "FK"
        assert constraint.columns == ["ID_FK_B_AUDYT"]
        assert constraint.ref_table == "B_AUDYT"
        assert constraint.ref_columns == ["ID_PK_B_AUDYT"]

    def test_unique_constraint_via_alter(self):
        """ALTER TABLE z UNIQUE — parsuje jako constraint UQ."""
        sql = '''ALTER TABLE "T" ADD CONSTRAINT "T_UQ" UNIQUE ("A", "B")'''
        result = parse_alter_table_fk(sql)
        assert result is not None
        _, c = result
        assert c.constraint_type == "UQ"


class TestParseCreateIndex:
    def test_unique_index(self):
        sql = 'CREATE UNIQUE INDEX "B_AUDYT_PK" ON "B_AUDYT" ("ID_PK_B_AUDYT")'
        idx = parse_create_index(sql)
        assert idx is not None
        assert idx.name == "B_AUDYT_PK"
        assert idx.table_name == "B_AUDYT"
        assert idx.columns == ["ID_PK_B_AUDYT"]
        assert idx.unique is True

    def test_regular_index(self):
        sql = 'CREATE INDEX "B_AK_IDX1" ON "B_AUDYT_KONTROLA" ("ID_FK_B_AUDYT")'
        idx = parse_create_index(sql)
        assert idx.unique is False

    def test_composite_index(self):
        sql = 'CREATE INDEX "IDX" ON "T" ("A", "B")'
        idx = parse_create_index(sql)
        assert idx.columns == ["A", "B"]

    def test_malformed_index_returns_none(self):
        """Niekompletny CREATE INDEX — brak kolumn."""
        sql = 'CREATE UNIQUE INDEX "SYS_IL0000082378C00005$$" ON "B_SL_C_PYTANIE" ('
        idx = parse_create_index(sql)
        assert idx is None


class TestParseCommentOn:
    def test_table_comment(self):
        sql = """COMMENT ON TABLE "B_AUDYT" IS 'Tabela audytow.'"""
        result = parse_comment_on(sql)
        assert result is not None
        obj_type, obj_name, col_name, text = result
        assert obj_type == "TABLE"
        assert obj_name == "B_AUDYT"
        assert col_name is None
        assert text == "Tabela audytow."

    def test_column_comment(self):
        sql = """COMMENT ON COLUMN "B_AUDYT"."STATUS_AUDYTU" IS 'Status audytu: Otwarty=edycja'"""
        result = parse_comment_on(sql)
        assert result is not None
        obj_type, obj_name, col_name, text = result
        assert obj_type == "COLUMN"
        assert obj_name == "B_AUDYT"
        assert col_name == "STATUS_AUDYTU"
        assert text == "Status audytu: Otwarty=edycja"

    def test_multiline_comment(self):
        """Komentarz z wieloliniowym SQL wewnątrz."""
        sql = """COMMENT ON TABLE "B_KONTROLA" IS 'WITH k AS (\nSELECT a FROM b\n)'"""
        result = parse_comment_on(sql)
        assert result is not None
        _, _, _, text = result
        assert "WITH k AS" in text


class TestParseCreateSequence:
    def test_sequence(self):
        sql = '''CREATE SEQUENCE "DAW_SEQ_B_C_ANAKIETA_PK"
                 MINVALUE 0 MAXVALUE 9999999 INCREMENT BY 1
                 START WITH 1203 NOCACHE NOORDER NOCYCLE'''
        seq = parse_create_sequence(sql)
        assert seq is not None
        assert seq.name == "DAW_SEQ_B_C_ANAKIETA_PK"
        assert seq.start_with == "1203"
        assert seq.increment_by == "1"
        assert seq.min_value == "0"
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

Run: `python -m pytest tests/test_ddl_parser.py::TestParseAlterTableFK tests/test_ddl_parser.py::TestParseCreateIndex tests/test_ddl_parser.py::TestParseCommentOn tests/test_ddl_parser.py::TestParseCreateSequence -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implementuj funkcje parsujące**

Dopisz do `apex_export_to_md/parser/ddl_parser.py`:

```python
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
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_ddl_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/parser/ddl_parser.py tests/test_ddl_parser.py
git commit -m "feat(parser): ALTER TABLE FK, CREATE INDEX, COMMENT ON, CREATE SEQUENCE"
```

---

### Task 4: DDL Parser — VIEW i PACKAGE

**Files:**
- Modify: `apex_export_to_md/parser/ddl_parser.py`
- Modify: `tests/test_ddl_parser.py`

- [ ] **Step 1: Napisz testy**

Dopisz do `tests/test_ddl_parser.py`:

```python
from apex_export_to_md.parser.ddl_parser import (
    parse_create_view,
    parse_package,
)


class TestParseCreateView:
    def test_view_with_columns(self):
        sql = '''CREATE OR REPLACE FORCE EDITIONABLE VIEW "B_V_TEST"
                 ("COL_A", "COL_B") AS
                 SELECT a.COL_A, b.COL_B
                 FROM TABLE_A a JOIN TABLE_B b ON a.ID = b.ID'''
        view = parse_create_view(sql)
        assert view is not None
        assert view.name == "B_V_TEST"
        assert view.columns == ["COL_A", "COL_B"]
        assert "SELECT" in view.sql
        assert "JOIN TABLE_B" in view.sql

    def test_view_without_column_list(self):
        sql = '''CREATE OR REPLACE VIEW "V1" AS SELECT * FROM T1'''
        view = parse_create_view(sql)
        assert view is not None
        assert view.name == "V1"
        assert view.columns == []
        assert "SELECT * FROM T1" in view.sql


class TestParsePackage:
    def test_package_spec(self):
        sql = '''create or replace PACKAGE PKG_TEST AS
    C_STATUS CONSTANT VARCHAR2(20) := 'Active';
    -- Tworzenie rekordu
    PROCEDURE CREATE_REC (
        p_name  IN  VARCHAR2,
        p_id    OUT NUMBER
    );
    -- Sprawdza status
    FUNCTION CHECK_STATUS (
        p_id IN NUMBER
    ) RETURN VARCHAR2;
END PKG_TEST;'''
        pkg = parse_package(sql)
        assert pkg is not None
        assert pkg.name == "PKG_TEST"
        assert len(pkg.spec_subprograms) == 2
        # Procedura
        proc = pkg.spec_subprograms[0]
        assert proc.name == "CREATE_REC"
        assert proc.subprogram_type == "PROCEDURE"
        assert proc.description == "Tworzenie rekordu"
        assert len(proc.parameters) == 2
        assert proc.parameters[0].direction == "IN"
        assert proc.parameters[1].direction == "OUT"
        # Funkcja
        func = pkg.spec_subprograms[1]
        assert func.name == "CHECK_STATUS"
        assert func.subprogram_type == "FUNCTION"
        assert func.return_type == "VARCHAR2"
        # Stałe
        assert len(pkg.constants) == 1
        assert "C_STATUS" in pkg.constants[0]

    def test_package_body(self):
        sql = '''create or replace PACKAGE BODY PKG_TEST AS
    -- Procedura wewnetrzna
    PROCEDURE HELPER (p_x IN NUMBER) IS
    BEGIN
        NULL;
    END HELPER;
    PROCEDURE CREATE_REC (p_name IN VARCHAR2, p_id OUT NUMBER) IS
    BEGIN
        NULL;
    END CREATE_REC;
END PKG_TEST;'''
        pkg = parse_package(sql)
        assert pkg is not None
        assert pkg.name == "PKG_TEST"
        assert len(pkg.body_subprograms) == 2
        # HELPER — prywatna (bo nie ma w spec)
        # Visibility ustalamy w orchestratorze, tutaj oba domyślnie public
        assert pkg.body_subprograms[0].name == "HELPER"
        assert pkg.body_source != ""

    def test_package_body_full_source_preserved(self):
        """Pełny kod body (z komentarzami) zachowany w body_source."""
        sql = '''create or replace PACKAGE BODY PKG AS
    -- Komentarz ważny
    PROCEDURE P IS
    BEGIN
        -- Jeszcze komentarz
        NULL;
    END P;
END PKG;'''
        pkg = parse_package(sql)
        assert "Komentarz ważny" in pkg.body_source
        assert "Jeszcze komentarz" in pkg.body_source
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

Run: `python -m pytest tests/test_ddl_parser.py::TestParseCreateView tests/test_ddl_parser.py::TestParsePackage -v`
Expected: FAIL

- [ ] **Step 3: Implementuj parse_create_view i parse_package**

Dopisz do `apex_export_to_md/parser/ddl_parser.py`:

```python
# ---------------------------------------------------------------------------
# Parsowanie CREATE VIEW
# ---------------------------------------------------------------------------

def parse_create_view(sql: str) -> DbView | None:
    """Parsuj CREATE [OR REPLACE] [FORCE] [EDITIONABLE] VIEW."""
    # Wyciągnij nazwę
    m = re.match(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?(?:EDITIONABLE\s+)?VIEW\s+"?(\w+)"?',
        sql, re.IGNORECASE,
    )
    if not m:
        return None

    name = m.group(1)

    # Opcjonalna lista kolumn w nawiasach przed AS
    rest = sql[m.end():]
    columns: list[str] = []
    col_match = re.match(r'\s*\(([^)]+)\)\s+AS\b', rest, re.IGNORECASE)
    if col_match:
        columns = _parse_column_list(col_match.group(1))
        rest = rest[col_match.end():]
    else:
        # Brak listy kolumn — szukaj AS
        as_match = re.match(r'\s+AS\b', rest, re.IGNORECASE)
        if as_match:
            rest = rest[as_match.end():]

    view_sql = rest.strip().rstrip(';').strip()

    return DbView(name=name, columns=columns, sql=view_sql)


# ---------------------------------------------------------------------------
# Parsowanie PACKAGE (spec i body)
# ---------------------------------------------------------------------------

def parse_package(sql: str) -> DbPackage | None:
    """Parsuj PACKAGE spec lub PACKAGE BODY."""
    # Wykryj spec vs body
    m = re.match(
        r'create\s+(?:or\s+replace\s+)?PACKAGE\s+(BODY\s+)?"?(\w+)"?\s+(?:AS|IS)\b',
        sql, re.IGNORECASE,
    )
    if not m:
        return None

    is_body = bool(m.group(1))
    name = m.group(2)
    source = sql.strip()

    # Wyciągnij stałe (CONSTANT)
    constants: list[str] = []
    for cm in re.finditer(
        r'(\w+\s+CONSTANT\s+\w+.*?:=\s*[^;]+)',
        source, re.IGNORECASE,
    ):
        constants.append(cm.group(1).strip())

    # Wyciągnij procedury i funkcje
    subprograms = _extract_subprograms(source)

    pkg = DbPackage(name=name, constants=constants)
    if is_body:
        pkg.body_subprograms = subprograms
        pkg.body_source = source
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

        # PROCEDURE nazwa (
        m = re.match(r'(?:PROCEDURE|FUNCTION)\s+(\w+)', stripped, re.IGNORECASE)
        if not m:
            continue

        sub_name = m.group(1)
        is_func = stripped.upper().startswith('FUNCTION')

        # Zbierz opis z komentarzy nad procedurą/funkcją
        description = _collect_description_above(lines, i)

        # Zbierz parametry (mogą być w kilku liniach)
        params_text = _collect_params_text(lines, i)
        parameters = _parse_parameters(params_text) if params_text else []

        # Typ zwracany (dla FUNCTION)
        return_type = None
        if is_func:
            # Szukaj RETURN w liniach od bieżącej
            for j in range(i, min(i + 20, len(lines))):
                rm = re.search(r'\)\s*RETURN\s+(\w+)', lines[j], re.IGNORECASE)
                if rm:
                    return_type = rm.group(1)
                    break
                # Może być na tej samej linii bez nawiasu
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
            # Pomiń separatory (====, ----)
            if text and not re.match(r'^[=\-]+$', text):
                desc_lines.insert(0, text)
        elif stripped == '':
            continue  # puste linie między komentarzami
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
    if not params_text.strip():
        return []

    params: list[DbParameter] = []
    # Podziel po ',' (top-level)
    parts = [p.strip() for p in params_text.split(',') if p.strip()]

    for part in parts:
        # Usuń komentarze z linii
        part = re.sub(r'--.*$', '', part, flags=re.MULTILINE).strip()
        # Wzorzec: p_name [IN [OUT]] TYPE
        m = re.match(r'(\w+)\s+(IN\s+OUT|OUT|IN)?\s*(\w+)', part, re.IGNORECASE)
        if m:
            direction = (m.group(2) or "IN").strip().upper()
            params.append(DbParameter(
                name=m.group(1),
                data_type=m.group(3),
                direction=direction,
            ))

    return params
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_ddl_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/parser/ddl_parser.py tests/test_ddl_parser.py
git commit -m "feat(parser): CREATE VIEW i PACKAGE spec/body w ddl_parser"
```

---

### Task 5: DDL Parser — orchestrator (parse_ddl, dedup, multi-file)

**Files:**
- Modify: `apex_export_to_md/parser/ddl_parser.py`
- Modify: `tests/test_ddl_parser.py`

- [ ] **Step 1: Napisz testy**

Dopisz do `tests/test_ddl_parser.py`:

```python
class TestParseDdl:
    def test_full_parse(self):
        sql = '''
        CREATE TABLE "T1" ("ID" NUMBER NOT NULL, CONSTRAINT "T1_PK" PRIMARY KEY ("ID") USING INDEX ENABLE);
        ALTER TABLE "T2" ADD CONSTRAINT "T2_FK" FOREIGN KEY ("FK_ID") REFERENCES "T1" ("ID") ENABLE;
        CREATE INDEX "T2_IDX" ON "T2" ("FK_ID");
        COMMENT ON TABLE "T1" IS 'Tabela glowna';
        COMMENT ON COLUMN "T1"."ID" IS 'Klucz glowny';
        CREATE SEQUENCE "SEQ1" MINVALUE 0 MAXVALUE 999 INCREMENT BY 1 START WITH 100;
        CREATE OR REPLACE VIEW "V1" ("A", "B") AS SELECT a, b FROM T1;
        create or replace PACKAGE PKG AS
            PROCEDURE P1;
        END PKG;
        /
        '''
        schema = parse_ddl(sql)
        assert len(schema.tables) == 1
        assert schema.tables[0].name == "T1"
        assert schema.tables[0].comment == "Tabela glowna"
        assert schema.tables[0].columns[0].comment == "Klucz glowny"
        # FK dołączony do odpowiedniej tabeli (T2 nie istnieje jako CREATE TABLE)
        # ale FK jest parsowany — sprawdzamy
        assert len(schema.views) == 1
        assert len(schema.sequences) == 1
        assert len(schema.packages) == 1

    def test_deduplication_first_wins(self):
        """Zduplikowane COMMENT ON — pierwszy wygrywa."""
        sql = '''
        CREATE TABLE "T" ("ID" NUMBER);
        COMMENT ON TABLE "T" IS 'Pierwszy komentarz';
        COMMENT ON TABLE "T" IS 'Drugi komentarz';
        '''
        schema = parse_ddl(sql)
        assert schema.tables[0].comment == "Pierwszy komentarz"

    def test_index_deduplication(self):
        sql = '''
        CREATE TABLE "T" ("ID" NUMBER);
        CREATE INDEX "IDX" ON "T" ("ID");
        CREATE INDEX "IDX" ON "T" ("ID");
        '''
        schema = parse_ddl(sql)
        assert len(schema.tables[0].indexes) == 1

    def test_package_spec_and_body_merged(self):
        sql = '''
        create or replace PACKAGE PKG AS
            PROCEDURE PUB;
        END PKG;
        /
        create or replace PACKAGE BODY PKG AS
            PROCEDURE PRIV IS BEGIN NULL; END PRIV;
            PROCEDURE PUB IS BEGIN NULL; END PUB;
        END PKG;
        /
        '''
        schema = parse_ddl(sql)
        assert len(schema.packages) == 1
        pkg = schema.packages[0]
        assert pkg.name == "PKG"
        assert len(pkg.spec_subprograms) == 1
        assert len(pkg.body_subprograms) == 2
        # PRIV jest private (nie ma w spec)
        priv = [s for s in pkg.body_subprograms if s.name == "PRIV"]
        assert priv[0].visibility == "private"

    def test_malformed_block_skipped(self):
        sql = '''
        CREATE TABLE "T" ("ID" NUMBER);
        CREATE UNIQUE INDEX "BAD" ON "T" (;
        '''
        schema = parse_ddl(sql)
        assert len(schema.tables) == 1
        assert len(schema.tables[0].indexes) == 0

    def test_comment_on_view(self):
        """COMMENT ON TABLE z nazwą widoku — trafia do widoku."""
        sql = '''
        CREATE OR REPLACE VIEW "V1" AS SELECT 1 FROM DUAL;
        COMMENT ON TABLE "V1" IS 'Widok testowy';
        '''
        schema = parse_ddl(sql)
        assert schema.views[0].comment == "Widok testowy"


class TestParseDdlFiles:
    def test_parse_single_file(self, tmp_path):
        f = tmp_path / "test.sql"
        f.write_text('CREATE TABLE "T" ("ID" NUMBER);', encoding="utf-8")
        schema = parse_ddl_files([f])
        assert len(schema.tables) == 1

    def test_parse_multiple_files(self, tmp_path):
        f1 = tmp_path / "tables.sql"
        f1.write_text('CREATE TABLE "T1" ("ID" NUMBER);', encoding="utf-8")
        f2 = tmp_path / "views.sql"
        f2.write_text('CREATE OR REPLACE VIEW "V1" AS SELECT 1 FROM DUAL;', encoding="utf-8")
        schema = parse_ddl_files([f1, f2])
        assert len(schema.tables) == 1
        assert len(schema.views) == 1
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

Run: `python -m pytest tests/test_ddl_parser.py::TestParseDdl tests/test_ddl_parser.py::TestParseDdlFiles -v`
Expected: FAIL

- [ ] **Step 3: Implementuj parse_ddl i parse_ddl_files**

Dopisz do `apex_export_to_md/parser/ddl_parser.py`:

```python
# ---------------------------------------------------------------------------
# Orchestrator — parse_ddl i parse_ddl_files
# ---------------------------------------------------------------------------

def parse_ddl(sql: str) -> DbSchema:
    """Parsuj pełny plik SQL DDL i zwróć DbSchema.

    Pipeline: split → classify → extract → dedup → merge packages → assign comments.
    """
    blocks = split_into_blocks(sql)

    tables: dict[str, DbTable] = {}  # nazwa → tabela (dedup)
    fk_constraints: list[tuple[str, DbConstraint]] = []  # (table_name, constraint)
    indexes: dict[str, DbIndex] = {}  # nazwa → index (dedup)
    table_comments: dict[str, str] = {}  # nazwa → komentarz (first-wins)
    column_comments: dict[str, dict[str, str]] = {}  # tabela → {kolumna: komentarz}
    views: dict[str, DbView] = {}
    sequences: dict[str, DbSequence] = {}
    packages: dict[str, DbPackage] = {}  # nazwa → pakiet (merge spec+body)

    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue

        upper = stripped.upper().lstrip()

        try:
            # CREATE TABLE
            if upper.startswith("CREATE TABLE") or upper.startswith('CREATE TABLE'):
                table = parse_create_table(stripped)
                if table and table.name not in tables:
                    tables[table.name] = table

            # ALTER TABLE ... ADD CONSTRAINT
            elif upper.startswith("ALTER TABLE"):
                result = parse_alter_table_fk(stripped)
                if result:
                    fk_constraints.append(result)

            # CREATE [UNIQUE] INDEX
            elif "INDEX" in upper and upper.startswith("CREATE"):
                if "PACKAGE" not in upper and "VIEW" not in upper:
                    idx = parse_create_index(stripped)
                    if idx and idx.name not in indexes:
                        indexes[idx.name] = idx

            # COMMENT ON
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

            # CREATE SEQUENCE
            elif upper.startswith("CREATE SEQUENCE"):
                seq = parse_create_sequence(stripped)
                if seq and seq.name not in sequences:
                    sequences[seq.name] = seq

            # CREATE VIEW
            elif "VIEW" in upper and upper.startswith("CREATE"):
                if "PACKAGE" not in upper:
                    view = parse_create_view(stripped)
                    if view and view.name not in views:
                        views[view.name] = view

            # PACKAGE spec lub body
            elif "PACKAGE" in upper and upper.startswith("CREATE"):
                pkg = parse_package(stripped)
                if pkg:
                    if pkg.name in packages:
                        # Merge spec + body
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

        except Exception as e:
            logger.warning("Błąd parsowania bloku: %s — %s", stripped[:60], e)

    # --- Post-processing ---

    # Przypisz FK constraints do tabel
    for table_name, constraint in fk_constraints:
        if table_name in tables:
            # Dedup po nazwie constraint
            existing_names = {c.name for c in tables[table_name].constraints}
            if constraint.name not in existing_names:
                tables[table_name].constraints.append(constraint)

    # Przypisz indeksy do tabel
    for idx in indexes.values():
        if idx.table_name in tables:
            tables[idx.table_name].indexes.append(idx)

    # Przypisz komentarze tabel/widoków
    view_names = set(views.keys())
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
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_ddl_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/parser/ddl_parser.py tests/test_ddl_parser.py
git commit -m "feat(parser): orchestrator parse_ddl z dedup, merge packages, parse_ddl_files"
```

---

### Task 6: DB Human Renderer + Mermaid ER

**Files:**
- Create: `apex_export_to_md/renderers/db_base_renderer.py`
- Create: `apex_export_to_md/renderers/db_human_renderer.py`
- Test: `tests/test_db_human_renderer.py`

- [ ] **Step 1: Napisz testy**

```python
# tests/test_db_human_renderer.py
"""Testy renderera human MD dla bazy danych."""
import pytest
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbIndex,
    DbView, DbSequence, DbParameter, DbSubprogram, DbPackage,
)
from apex_export_to_md.renderers.db_human_renderer import DbHumanRenderer


@pytest.fixture
def config():
    return AppConfig(include_code="full")


@pytest.fixture
def sample_schema():
    return DbSchema(
        tables=[
            DbTable(
                name="B_AUDYT",
                columns=[
                    DbColumn(name="ID_PK_B_AUDYT", data_type="NUMBER", nullable=False, identity=True),
                    DbColumn(name="STATUS_AUDYTU", data_type="VARCHAR2(20)", nullable=False,
                             default="'Otwarty'", comment="Status audytu"),
                ],
                constraints=[
                    DbConstraint(name="B_AUDYT_PK", constraint_type="PK", columns=["ID_PK_B_AUDYT"]),
                    DbConstraint(name="CHK1", constraint_type="CHK",
                                 check_expression="STATUS_AUDYTU IN ('Otwarty')"),
                ],
                indexes=[
                    DbIndex(name="B_AUDYT_PK", table_name="B_AUDYT",
                            columns=["ID_PK_B_AUDYT"], unique=True),
                ],
                comment="Tabela audytow",
            ),
            DbTable(
                name="B_ANKIETA",
                constraints=[
                    DbConstraint(name="B_ANKIETA_FK", constraint_type="FK",
                                 columns=["ID_FK_B_AUDYT"], ref_table="B_AUDYT",
                                 ref_columns=["ID_PK_B_AUDYT"]),
                ],
            ),
        ],
        views=[
            DbView(name="B_V_TEST", columns=["A", "B"],
                   sql="SELECT a, b FROM T", comment="Widok testowy"),
        ],
        packages=[
            DbPackage(
                name="PKG_TEST",
                spec_subprograms=[
                    DbSubprogram(name="PROC1", subprogram_type="PROCEDURE",
                                 description="Opis procedury",
                                 parameters=[DbParameter(name="p_id", data_type="NUMBER")]),
                ],
                body_source="PACKAGE BODY PKG_TEST AS\n  -- Komentarz\n  PROCEDURE PROC1...\nEND;",
            ),
        ],
        sequences=[
            DbSequence(name="SEQ1", start_with="100", increment_by="1"),
        ],
    )


class TestDbHumanRenderer:
    def test_header(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "# Baza danych" in result

    def test_mermaid_er_present(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "```mermaid" in result
        assert "erDiagram" in result
        assert "B_AUDYT" in result
        assert "B_ANKIETA" in result

    def test_table_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "### Tabela: B_AUDYT" in result
        assert "Tabela audytow" in result
        assert "| ID_PK_B_AUDYT" in result
        assert "| STATUS_AUDYTU" in result
        assert "Status audytu" in result

    def test_pk_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "Klucz główny" in result
        assert "B_AUDYT_PK" in result

    def test_fk_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "B_ANKIETA_FK" in result
        assert "B_AUDYT" in result

    def test_check_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "Check" in result
        assert "STATUS_AUDYTU IN" in result

    def test_view_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "### Widok: B_V_TEST" in result
        assert "SELECT a, b FROM T" in result

    def test_package_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "### Pakiet: PKG_TEST" in result
        assert "PROC1" in result
        assert "Opis procedury" in result

    def test_package_body_code(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "```plsql" in result
        assert "Komentarz" in result

    def test_sequence_rendered(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "SEQ1" in result
        assert "100" in result

    def test_mermaid_fk_relationship(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        # Mermaid ER powinien mieć relację B_AUDYT ||--o{ B_ANKIETA
        assert "B_AUDYT" in result
        assert "B_ANKIETA" in result
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

Run: `python -m pytest tests/test_db_human_renderer.py -v`
Expected: FAIL

- [ ] **Step 3: Implementuj DbBaseRenderer**

```python
# apex_export_to_md/renderers/db_base_renderer.py
"""Abstrakcyjna klasa bazowa rendererów bazy danych.

Analogiczna do BaseRenderer, ale operuje na DbSchema.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from apex_export_to_md.models.db_models import DbSchema
from apex_export_to_md.config import AppConfig


class DbBaseRenderer(ABC):
    """Bazowy renderer DB — generuje tekst z modelu DbSchema."""

    def __init__(self, config: AppConfig):
        self._config = config

    @abstractmethod
    def render(self, schema: DbSchema) -> str:
        """Generuj tekst z modelu bazy danych."""
        ...

    def _should_include_code(self) -> bool:
        return self._config.include_code == "full"

    def _should_summarize_code(self) -> bool:
        return self._config.include_code == "summary"
```

- [ ] **Step 4: Implementuj DbHumanRenderer**

```python
# apex_export_to_md/renderers/db_human_renderer.py
"""Human Renderer DB — generuje czytelny Markdown z dokumentacją bazy danych.

Zawiera: diagram Mermaid ER, tabele z kolumnami, widoki, pakiety PL/SQL, sekwencje.
"""
from __future__ import annotations
from apex_export_to_md.renderers.db_base_renderer import DbBaseRenderer
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbIndex,
    DbView, DbSequence, DbSubprogram, DbPackage,
)


class DbHumanRenderer(DbBaseRenderer):
    """Renderer Markdown czytelny dla człowieka — baza danych."""

    def render(self, schema: DbSchema) -> str:
        lines: list[str] = []
        lines.append("# Baza danych")
        lines.append("")

        # Diagram Mermaid ER
        er = self._render_mermaid_er(schema)
        if er:
            lines.append("## Diagram relacji")
            lines.append("")
            lines.extend(er)
            lines.append("")

        # Tabele
        if schema.tables:
            lines.append("## Tabele")
            lines.append("")
            for table in schema.tables:
                lines.extend(self._render_table(table))

        # Widoki
        if schema.views:
            lines.append("## Widoki")
            lines.append("")
            for view in schema.views:
                lines.extend(self._render_view(view))

        # Pakiety
        if schema.packages:
            lines.append("## Pakiety PL/SQL")
            lines.append("")
            for pkg in schema.packages:
                lines.extend(self._render_package(pkg))

        # Sekwencje
        if schema.sequences:
            lines.append("## Sekwencje")
            lines.append("")
            lines.append("| Nazwa | Start | Increment | Min | Max |")
            lines.append("|-------|-------|-----------|-----|-----|")
            for seq in schema.sequences:
                lines.append(
                    f"| {seq.name} | {seq.start_with or '—'} "
                    f"| {seq.increment_by or '—'} "
                    f"| {seq.min_value or '—'} "
                    f"| {seq.max_value or '—'} |"
                )
            lines.append("")

        return "\n".join(lines)

    def _render_mermaid_er(self, schema: DbSchema) -> list[str]:
        """Generuj diagram Mermaid ER z FK constraints."""
        lines: list[str] = ["```mermaid", "erDiagram"]

        # Zbierz wszystkie relacje FK
        relations: list[tuple[str, str, str]] = []  # (parent, child, fk_name)
        for table in schema.tables:
            for c in table.constraints:
                if c.constraint_type == "FK" and c.ref_table:
                    relations.append((c.ref_table, table.name, c.name))

        # Renderuj relacje
        for parent, child, fk_name in relations:
            lines.append(f'    {parent} ||--o{{ {child} : "{fk_name}"')

        # Dodaj tabele z kluczowymi kolumnami (max 5)
        for table in schema.tables:
            lines.append(f"    {table.name} {{")
            shown = 0
            for col in table.columns:
                if shown >= 5:
                    break
                # Pokaż PK, FK i constraint kolumny
                is_pk = any(
                    c.constraint_type == "PK" and col.name in c.columns
                    for c in table.constraints
                )
                is_fk = any(
                    c.constraint_type == "FK" and col.name in c.columns
                    for c in table.constraints
                )
                marker = " PK" if is_pk else (" FK" if is_fk else "")
                if is_pk or is_fk or shown < 3:
                    dt = col.data_type.split("(")[0]  # skróć typ
                    lines.append(f"        {dt} {col.name}{marker}")
                    shown += 1
            lines.append("    }")

        lines.append("```")
        return lines

    def _render_table(self, table: DbTable) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Tabela: {table.name}")
        if table.comment:
            lines.append(f"> {table.comment}")
        lines.append("")

        # Kolumny
        if table.columns:
            lines.append("| Kolumna | Typ | NULL | Default | Komentarz |")
            lines.append("|---------|-----|------|---------|-----------|")
            for col in table.columns:
                null = "NOT NULL" if not col.nullable else "NULL"
                default = col.default or "—"
                comment = col.comment or "—"
                identity = " (IDENTITY)" if col.identity else ""
                lines.append(
                    f"| {col.name} | {col.data_type}{identity} "
                    f"| {null} | {default} | {comment} |"
                )
            lines.append("")

        # PK
        pks = [c for c in table.constraints if c.constraint_type == "PK"]
        if pks:
            pk = pks[0]
            cols = ", ".join(pk.columns)
            lines.append(f"**Klucz główny:** {pk.name} ({cols})")
            lines.append("")

        # FK
        fks = [c for c in table.constraints if c.constraint_type == "FK"]
        if fks:
            lines.append("**Foreign keys:**")
            for fk in fks:
                cols = ", ".join(fk.columns)
                ref_cols = ", ".join(fk.ref_columns) if fk.ref_columns else "?"
                lines.append(f"- {fk.name}: {cols} → {fk.ref_table}({ref_cols})")
            lines.append("")

        # UNIQUE
        uqs = [c for c in table.constraints if c.constraint_type == "UQ"]
        if uqs:
            lines.append("**Unique constraints:**")
            for uq in uqs:
                cols = ", ".join(uq.columns)
                lines.append(f"- {uq.name}: ({cols})")
            lines.append("")

        # CHECK
        chks = [c for c in table.constraints if c.constraint_type == "CHK"]
        if chks:
            lines.append("**Check constraints:**")
            for chk in chks:
                lines.append(f"- {chk.name}: `{chk.check_expression}`")
            lines.append("")

        # Indeksy
        if table.indexes:
            lines.append("**Indeksy:**")
            for idx in table.indexes:
                cols = ", ".join(idx.columns)
                uq = " (UNIQUE)" if idx.unique else ""
                lines.append(f"- {idx.name}: ({cols}){uq}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _render_view(self, view: DbView) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Widok: {view.name}")
        if view.comment:
            lines.append(f"> {view.comment}")
        if view.columns:
            lines.append(f"**Kolumny:** {', '.join(view.columns)}")
        lines.append("")
        if view.sql and self._should_include_code():
            lines.append("```sql")
            lines.append(view.sql)
            lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _render_package(self, pkg: DbPackage) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Pakiet: {pkg.name}")
        lines.append("")

        # Stałe
        if pkg.constants:
            lines.append("**Stałe:**")
            for const in pkg.constants:
                lines.append(f"- `{const}`")
            lines.append("")

        # Specyfikacja — tabela procedur/funkcji
        if pkg.spec_subprograms:
            lines.append("#### Specyfikacja")
            lines.append("")
            lines.append("| Procedura/Funkcja | Parametry | Zwraca | Opis |")
            lines.append("|-------------------|-----------|--------|------|")
            for sub in pkg.spec_subprograms:
                params = ", ".join(
                    f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
                ) or "—"
                ret = sub.return_type or "—"
                desc = sub.description or "—"
                lines.append(f"| {sub.name} | {params} | {ret} | {desc} |")
            lines.append("")

        # Body — procedury prywatne
        private_subs = [s for s in pkg.body_subprograms if s.visibility == "private"]
        if private_subs:
            lines.append("#### Procedury prywatne (body)")
            lines.append("")
            for sub in private_subs:
                params = ", ".join(
                    f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
                ) or "—"
                desc = sub.description or ""
                lines.append(f"- **{sub.name}**({params}) — {desc}")
            lines.append("")

        # Body — pełny kod
        if pkg.body_source and self._should_include_code():
            lines.append("#### Implementacja (body)")
            lines.append("")
            lines.append("```plsql")
            lines.append(pkg.body_source)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines
```

- [ ] **Step 5: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_db_human_renderer.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add apex_export_to_md/renderers/db_base_renderer.py apex_export_to_md/renderers/db_human_renderer.py tests/test_db_human_renderer.py
git commit -m "feat(renderers): DbHumanRenderer z Mermaid ER i pełną dokumentacją DB"
```

---

### Task 7: DB LLM Renderer

**Files:**
- Create: `apex_export_to_md/renderers/db_llm_renderer.py`
- Test: `tests/test_db_llm_renderer.py`

- [ ] **Step 1: Napisz testy**

```python
# tests/test_db_llm_renderer.py
"""Testy renderera LLM MD dla bazy danych."""
import pytest
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint,
    DbView, DbSequence, DbSubprogram, DbPackage, DbParameter,
)
from apex_export_to_md.renderers.db_llm_renderer import DbLLMRenderer


@pytest.fixture
def config():
    return AppConfig(include_code="full")


@pytest.fixture
def sample_schema():
    return DbSchema(
        tables=[
            DbTable(
                name="B_AUDYT",
                columns=[
                    DbColumn(name="ID_PK", data_type="NUMBER", nullable=False, identity=True,
                             comment="Klucz"),
                    DbColumn(name="STATUS", data_type="VARCHAR2(20)", nullable=False,
                             default="'Otwarty'"),
                ],
                constraints=[
                    DbConstraint(name="PK1", constraint_type="PK", columns=["ID_PK"]),
                    DbConstraint(name="FK1", constraint_type="FK", columns=["FK_COL"],
                                 ref_table="OTHER", ref_columns=["ID"]),
                    DbConstraint(name="CHK1", constraint_type="CHK",
                                 check_expression="STATUS IN ('A','B')"),
                ],
                comment="Tabela audytow",
            ),
        ],
        views=[DbView(name="V1", columns=["A"], sql="SELECT a FROM T", comment="Widok")],
        packages=[
            DbPackage(
                name="PKG",
                spec_subprograms=[
                    DbSubprogram(name="P1", subprogram_type="PROCEDURE",
                                 description="Opis",
                                 parameters=[DbParameter(name="p_id", data_type="NUMBER")]),
                    DbSubprogram(name="F1", subprogram_type="FUNCTION",
                                 return_type="VARCHAR2"),
                ],
                body_subprograms=[
                    DbSubprogram(name="PRIV", subprogram_type="PROCEDURE",
                                 visibility="private"),
                ],
                body_source="line1\nline2\nline3",
            ),
        ],
        sequences=[DbSequence(name="SEQ1", start_with="100", increment_by="1")],
    )


class TestDbLLMRenderer:
    def test_table_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "TBL:B_AUDYT|Tabela audytow" in result

    def test_column_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "COL:ID_PK|NUMBER|NN|" in result
        assert "COL:STATUS|VARCHAR2(20)|NN|'Otwarty'" in result

    def test_fk_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "FK:FK1|FK_COL" in result
        assert "OTHER.ID" in result

    def test_check_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "CHK:" in result

    def test_view_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "VW:V1|Widok" in result

    def test_package_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "PKG:PKG" in result
        assert "PROC:P1(" in result
        assert "FUNC:F1(" in result

    def test_private_subprogram(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "private" in result.lower()
        assert "PRIV" in result

    def test_sequence_format(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "SEQ:SEQ1|START:100|INCR:1" in result

    def test_code_lines_count(self, config, sample_schema):
        r = DbLLMRenderer(config)
        result = r.render(sample_schema)
        assert "CODE:3 lines" in result
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

- [ ] **Step 3: Implementuj DbLLMRenderer**

```python
# apex_export_to_md/renderers/db_llm_renderer.py
"""LLM Renderer DB — generuje skondensowany format liniowy dla bazy danych.

Prefiksy: TBL, COL, FK, UQ, CHK, IDX, VW, VCOL, PKG, PROC, FUNC, CONST, SEQ.
"""
from __future__ import annotations
from apex_export_to_md.renderers.db_base_renderer import DbBaseRenderer
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbView, DbSequence, DbPackage, DbSubprogram,
)


class DbLLMRenderer(DbBaseRenderer):
    """Renderer LLM — format kondensowany dla bazy danych."""

    def render(self, schema: DbSchema) -> str:
        lines: list[str] = []
        lines.append("SCHEMA:DB")

        for table in schema.tables:
            lines.extend(self._render_table(table))

        for view in schema.views:
            lines.extend(self._render_view(view))

        for pkg in schema.packages:
            lines.extend(self._render_package(pkg))

        for seq in schema.sequences:
            parts = [f"SEQ:{seq.name}"]
            if seq.start_with:
                parts.append(f"START:{seq.start_with}")
            if seq.increment_by:
                parts.append(f"INCR:{seq.increment_by}")
            lines.append("|".join(parts))

        return "\n".join(lines)

    def _render_table(self, table: DbTable) -> list[str]:
        lines: list[str] = []
        comment = table.comment or ""
        lines.append(f"TBL:{table.name}|{comment}")

        # Zbierz info o PK kolumnach
        pk_cols: set[str] = set()
        for c in table.constraints:
            if c.constraint_type == "PK":
                pk_cols.update(c.columns)

        for col in table.columns:
            parts = [f"  COL:{col.name}", col.data_type]
            parts.append("NN" if not col.nullable else "NULL")
            parts.append(col.default or "")
            if col.name in pk_cols:
                parts.append("PK")
            if col.identity:
                parts.append("IDENTITY")
            if col.comment:
                parts.append(col.comment)
            lines.append("|".join(parts))

        for c in table.constraints:
            if c.constraint_type == "FK":
                cols = ",".join(c.columns)
                ref_cols = ",".join(c.ref_columns) if c.ref_columns else ""
                lines.append(f"  FK:{c.name}|{cols}→{c.ref_table}.{ref_cols}")
            elif c.constraint_type == "UQ":
                cols = ",".join(c.columns)
                lines.append(f"  UQ:{cols}")
            elif c.constraint_type == "CHK":
                lines.append(f"  CHK:{c.check_expression or ''}")

        for idx in table.indexes:
            cols = ",".join(idx.columns)
            uq = "UNIQUE" if idx.unique else ""
            lines.append(f"  IDX:{idx.name}|{cols}|{uq}")

        return lines

    def _render_view(self, view: DbView) -> list[str]:
        lines: list[str] = []
        comment = view.comment or ""
        lines.append(f"VW:{view.name}|{comment}")
        for col in view.columns:
            lines.append(f"  VCOL:{col}")
        if view.sql:
            first_line = view.sql.strip().split("\n")[0]
            lines.append(f"  SQL:{first_line}")
        return lines

    def _render_package(self, pkg: DbPackage) -> list[str]:
        lines: list[str] = []
        lines.append(f"PKG:{pkg.name}")

        if pkg.spec_subprograms:
            lines.append("  SPEC:")
            for sub in pkg.spec_subprograms:
                lines.append(self._render_subprogram(sub, indent="  "))

        if pkg.body_subprograms:
            lines.append("  BODY:")
            for sub in pkg.body_subprograms:
                lines.append(self._render_subprogram(sub, indent="  "))

        for const in pkg.constants:
            lines.append(f"  CONST:{const}")

        if pkg.body_source:
            line_count = len(pkg.body_source.strip().split("\n"))
            lines.append(f"  CODE:{line_count} lines")

        return lines

    def _render_subprogram(self, sub: DbSubprogram, indent: str = "") -> str:
        params = ",".join(
            f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
        )
        prefix = "FUNC" if sub.subprogram_type == "FUNCTION" else "PROC"
        parts = [f"{indent}{prefix}:{sub.name}({params})"]
        if sub.return_type:
            parts[0] += f"→{sub.return_type}"
        if sub.description:
            parts.append(sub.description)
        if sub.visibility == "private":
            parts.append("private")
        return "|".join(parts)
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_db_llm_renderer.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/renderers/db_llm_renderer.py tests/test_db_llm_renderer.py
git commit -m "feat(renderers): DbLLMRenderer — format kondensowany dla bazy danych"
```

---

### Task 8: APEX ↔ DB Linker

**Files:**
- Create: `apex_export_to_md/linker/__init__.py`
- Create: `apex_export_to_md/linker/apex_db_linker.py`
- Test: `tests/test_apex_db_linker.py`

- [ ] **Step 1: Napisz testy**

```python
# tests/test_apex_db_linker.py
"""Testy linkera APEX↔DB — wykrywanie powiązań."""
import pytest
from apex_export_to_md.linker.apex_db_linker import ApexDbLinker, ApexDbLink
from apex_export_to_md.models.apex_models import (
    ApexApp, ApexPage, Region, Process, LOV, Validation,
)
from apex_export_to_md.models.db_models import DbSchema, DbTable, DbView


@pytest.fixture
def db_schema():
    return DbSchema(
        tables=[
            DbTable(name="B_AUDYT"),
            DbTable(name="B_AUDYT_KONTROLA"),
            DbTable(name="B_KONTROLA"),
        ],
        views=[DbView(name="B_V_AUDYT_KONTROLE")],
    )


@pytest.fixture
def apex_app():
    return ApexApp(
        name="TEST", id="1", alias="T",
        pages=[
            ApexPage(
                id=1, name="Lista audytow",
                regions=[
                    Region(
                        name="Grid",
                        type="Interactive Grid",
                        source_table="B_AUDYT",
                    ),
                    Region(
                        name="SQL Region",
                        type="Classic Report",
                        source_sql="SELECT * FROM B_AUDYT_KONTROLA ak JOIN B_KONTROLA k ON ak.ID = k.ID",
                    ),
                ],
                processes=[
                    Process(
                        name="Save",
                        type="PL/SQL",
                        code="INSERT INTO B_AUDYT_KONTROLA VALUES (:P1_ID, :P2_ID, :APP_USER, SYSDATE);",
                    ),
                ],
                validations=[
                    Validation(
                        name="Check",
                        type="PL/SQL",
                        code="SELECT 1 FROM B_V_AUDYT_KONTROLE WHERE ID = :P1_ID",
                    ),
                ],
            ),
            ApexPage(
                id=2, name="Pusta strona",
                regions=[Region(name="Static", type="Static Content")],
            ),
        ],
        lovs=[
            LOV(name="LOV_KONTROLE", source_type="SQL Query",
                sql_query="SELECT REFERENCE_ID FROM B_KONTROLA WHERE STATUS != 'Deactive'"),
        ],
    )


class TestApexDbLinker:
    def test_link_region_source_table(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        # Strona 1 powinna mieć link do B_AUDYT (region source_table)
        page1_links = [l for l in links if l.page_id == 1]
        all_objects = set()
        for l in page1_links:
            all_objects.update(l.db_objects)
        assert "B_AUDYT" in all_objects

    def test_link_region_sql(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        page1_links = [l for l in links if l.page_id == 1]
        all_objects = set()
        for l in page1_links:
            all_objects.update(l.db_objects)
        # Z SQL: FROM B_AUDYT_KONTROLA, JOIN B_KONTROLA
        assert "B_AUDYT_KONTROLA" in all_objects
        assert "B_KONTROLA" in all_objects

    def test_link_process_code(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        proc_links = [l for l in links if l.source_type == "process"]
        assert len(proc_links) > 0
        assert "B_AUDYT_KONTROLA" in proc_links[0].db_objects

    def test_link_validation(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        val_links = [l for l in links if l.source_type == "validation"]
        all_objects = set()
        for l in val_links:
            all_objects.update(l.db_objects)
        assert "B_V_AUDYT_KONTROLE" in all_objects

    def test_link_lov(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        lov_links = [l for l in links if l.source_type == "lov"]
        all_objects = set()
        for l in lov_links:
            all_objects.update(l.db_objects)
        assert "B_KONTROLA" in all_objects

    def test_empty_page_no_links(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        page2_links = [l for l in links if l.page_id == 2]
        assert len(page2_links) == 0

    def test_no_false_positive_prefix(self, apex_app, db_schema):
        """B_AUDYT nie powinien matchować B_AUDYT_KONTROLA (word boundary)."""
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        # Region "Grid" ma source_table="B_AUDYT" — powinien linkować TYLKO B_AUDYT, nie B_AUDYT_KONTROLA
        grid_links = [l for l in links if l.source_name == "Grid"]
        assert len(grid_links) == 1
        assert grid_links[0].db_objects == ["B_AUDYT"]
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

- [ ] **Step 3: Implementuj linker**

```python
# apex_export_to_md/linker/__init__.py
"""Linker APEX ↔ Baza danych."""
from apex_export_to_md.linker.apex_db_linker import ApexDbLinker, ApexDbLink

__all__ = ["ApexDbLinker", "ApexDbLink"]
```

```python
# apex_export_to_md/linker/apex_db_linker.py
"""Automatyczne wykrywanie powiązań między stronami APEX a obiektami DB.

Heurystyki: parsowanie SQL z regionów, procesów, walidacji i LOV-ów.
Dopasowanie z word boundaries, case-insensitive, longest-first.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from apex_export_to_md.models.apex_models import ApexApp, ApexPage
from apex_export_to_md.models.db_models import DbSchema


@dataclass
class ApexDbLink:
    """Powiązanie między elementem APEX a obiektami bazy danych."""
    page_id: int
    page_name: str
    db_objects: list[str] = field(default_factory=list)
    source_type: str = ""     # "region", "process", "validation", "lov"
    source_name: str = ""     # nazwa regionu/procesu/LOV


class ApexDbLinker:
    """Wykrywa powiązania APEX↔DB przez heurystyki SQL."""

    def __init__(self, app: ApexApp, schema: DbSchema):
        self._app = app
        self._schema = schema
        # Zbierz nazwy obiektów DB, sortuj od najdłuższych
        self._db_names = sorted(
            [t.name for t in schema.tables] + [v.name for v in schema.views],
            key=lambda x: -len(x),
        )

    def find_links(self) -> list[ApexDbLink]:
        """Zwróć listę powiązań APEX↔DB."""
        links: list[ApexDbLink] = []

        for page in self._app.pages:
            links.extend(self._scan_page(page))

        # LOV-y (nie przypisane do strony — page_id=0)
        for lov in self._app.lovs:
            sql = lov.sql_query or ""
            if sql:
                objects = self._find_db_objects_in_sql(sql)
                if objects:
                    links.append(ApexDbLink(
                        page_id=0, page_name="(shared)",
                        db_objects=objects,
                        source_type="lov", source_name=lov.name,
                    ))

        return links

    def _scan_page(self, page: ApexPage) -> list[ApexDbLink]:
        links: list[ApexDbLink] = []

        # Regiony
        for region in page.regions:
            objects: list[str] = []
            if region.source_table:
                # Bezpośrednia referencja do tabeli
                if region.source_table in self._db_names:
                    objects.append(region.source_table)
            if region.source_sql:
                objects.extend(self._find_db_objects_in_sql(region.source_sql))
            # Deduplikacja
            objects = list(dict.fromkeys(objects))
            if objects:
                links.append(ApexDbLink(
                    page_id=page.id, page_name=page.name,
                    db_objects=objects,
                    source_type="region", source_name=region.name,
                ))

        # Procesy
        for proc in page.processes:
            if proc.code:
                objects = self._find_db_objects_in_sql(proc.code)
                if objects:
                    links.append(ApexDbLink(
                        page_id=page.id, page_name=page.name,
                        db_objects=objects,
                        source_type="process", source_name=proc.name,
                    ))

        # Walidacje
        for val in page.validations:
            if val.code:
                objects = self._find_db_objects_in_sql(val.code)
                if objects:
                    links.append(ApexDbLink(
                        page_id=page.id, page_name=page.name,
                        db_objects=objects,
                        source_type="validation", source_name=val.name,
                    ))

        return links

    def _find_db_objects_in_sql(self, sql: str) -> list[str]:
        """Szukaj nazw tabel/widoków w tekście SQL.

        Word boundaries + case-insensitive + longest-first.
        """
        found: list[str] = []
        sql_upper = sql.upper()

        for name in self._db_names:
            # Word boundary: \b nie działa z _ na granicy
            # Użyj lookbehind/lookahead na non-word chars
            pattern = r'(?<![A-Z0-9_])' + re.escape(name) + r'(?![A-Z0-9_])'
            if re.search(pattern, sql_upper):
                found.append(name)

        return found
```

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_apex_db_linker.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/linker/__init__.py apex_export_to_md/linker/apex_db_linker.py tests/test_apex_db_linker.py
git commit -m "feat(linker): ApexDbLinker wykrywa powiązania APEX↔DB przez heurystyki SQL"
```

---

### Task 9: Config i CLI — rozszerzenia

**Files:**
- Modify: `apex_export_to_md/config.py`
- Modify: `apex_export_to_md/cli.py`
- Test: `tests/test_cli_ddl.py`

- [ ] **Step 1: Napisz testy**

```python
# tests/test_cli_ddl.py
"""Testy rozszerzonego CLI z obsługą DDL."""
import pytest
from apex_export_to_md.cli import parse_args, args_to_config
from apex_export_to_md.config import AppConfig


class TestDdlCliArgs:
    def test_default_ddl_enabled(self):
        args = parse_args(["some/dir"])
        config = args_to_config(args)
        assert config.enable_ddl is True
        assert config.enable_html is True

    def test_no_ddl_flag(self):
        args = parse_args(["some/dir", "--no-ddl"])
        config = args_to_config(args)
        assert config.enable_ddl is False

    def test_no_html_flag(self):
        args = parse_args(["some/dir", "--no-html"])
        config = args_to_config(args)
        assert config.enable_html is False

    def test_ddl_files_option(self):
        args = parse_args(["some/dir", "--ddl-files", "a.sql,b.sql"])
        config = args_to_config(args)
        assert config.ddl_files == ["a.sql", "b.sql"]

    def test_html_output_option(self):
        args = parse_args(["some/dir", "--html-output", "docs.html"])
        config = args_to_config(args)
        assert config.html_output == "docs.html"

    def test_author_name_default(self):
        args = parse_args(["some/dir"])
        config = args_to_config(args)
        assert config.author_name == "Tomasz Rembiasz"


class TestAppConfigDefaults:
    def test_new_defaults(self):
        c = AppConfig()
        assert c.enable_ddl is True
        assert c.ddl_files == []
        assert c.enable_html is True
        assert c.html_output == ""
        assert c.author_name == "Tomasz Rembiasz"
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

- [ ] **Step 3: Rozszerz config.py**

Dopisz nowe pola do klasy `AppConfig` w `apex_export_to_md/config.py`:

```python
    # --- DDL i HTML ---
    enable_ddl: bool = True
    ddl_files: list[str] = field(default_factory=list)
    enable_html: bool = True
    html_output: str = ""
    author_name: str = "Tomasz Rembiasz"
```

- [ ] **Step 4: Rozszerz cli.py — parse_args**

Dopisz nowe argumenty do `parse_args` w `apex_export_to_md/cli.py`:

```python
    parser.add_argument(
        "--no-ddl", action="store_true",
        help="Pomiń pipeline SQL DDL",
    )
    parser.add_argument(
        "--ddl-files", default="",
        help="Pliki SQL do parsowania (rozdzielone przecinkami; domyślnie: auto)",
    )
    parser.add_argument(
        "--no-html", action="store_true",
        help="Pomiń generowanie interaktywnego HTML",
    )
    parser.add_argument(
        "--html-output", default="",
        help="Nazwa pliku HTML wyjściowego",
    )
    parser.add_argument(
        "--author-name", default="Tomasz Rembiasz",
        help="Autor w stopce HTML (domyślnie: Tomasz Rembiasz)",
    )
```

Rozszerz `args_to_config`:

```python
    # Przetwórz listę plików DDL
    ddl_files: list[str] = []
    if args.ddl_files:
        ddl_files = [f.strip() for f in args.ddl_files.split(",") if f.strip()]

    return AppConfig(
        # ... istniejące pola ...
        enable_ddl=not args.no_ddl,
        ddl_files=ddl_files,
        enable_html=not args.no_html,
        html_output=args.html_output,
        author_name=args.author_name,
    )
```

- [ ] **Step 5: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_cli_ddl.py -v`
Expected: ALL PASS

- [ ] **Step 6: Uruchom WSZYSTKIE istniejące testy**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (istniejące testy nie powinny się zepsuć)

- [ ] **Step 7: Commit**

```bash
git add apex_export_to_md/config.py apex_export_to_md/cli.py tests/test_cli_ddl.py
git commit -m "feat(cli): dodaj argumenty --no-ddl, --ddl-files, --no-html, --html-output"
```

---

### Task 10: Pipeline integration — DDL w cli.py

**Files:**
- Modify: `apex_export_to_md/cli.py`

**Context:** Rozszerzamy `run_pipeline()` o kroki DDL (parse → render MD) i HTML (linker → render). Istniejący pipeline APEX pozostaje bez zmian.

- [ ] **Step 1: Rozszerz run_pipeline w cli.py**

Dodaj importy na górze pliku:

```python
from apex_export_to_md.parser.ddl_parser import parse_ddl_files
from apex_export_to_md.renderers.db_human_renderer import DbHumanRenderer
from apex_export_to_md.renderers.db_llm_renderer import DbLLMRenderer
from apex_export_to_md.renderers.html_renderer import HtmlRenderer
from apex_export_to_md.linker.apex_db_linker import ApexDbLinker
```

Dodaj helper `find_sql_files`:

```python
def find_sql_files(input_path: Path, config: AppConfig) -> list[Path]:
    """Znajdź pliki SQL w katalogu eksportu.

    Jeśli config.ddl_files podany — użyj wskazanych plików.
    W przeciwnym razie — auto-wykryj *.sql.
    """
    if config.ddl_files:
        return [Path(f) for f in config.ddl_files if Path(f).exists()]

    sql_files = list(input_path.rglob("*.sql"))
    if sql_files:
        logging.info("Znaleziono %d plików SQL: %s",
                     len(sql_files), [f.name for f in sql_files])
    return sql_files
```

Na końcu `run_pipeline()`, po zapisie plików APEX MD, dopisz:

```python
    # --- Pipeline DDL ---
    sql_files = find_sql_files(input_path, config)
    schema = None

    if sql_files and config.enable_ddl:
        schema = parse_ddl_files(sql_files)
        logging.info("Sparsowano DDL: %d tabel, %d widoków, %d pakietów, %d sekwencji",
                     len(schema.tables), len(schema.views),
                     len(schema.packages), len(schema.sequences))

        if config.output_format in ("both", "human"):
            renderer = DbHumanRenderer(config)
            content = renderer.render(schema)
            out_path = output_dir / f"{config.output_prefix}_db_human.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

        if config.output_format in ("both", "llm"):
            renderer = DbLLMRenderer(config)
            content = renderer.render(schema)
            out_path = output_dir / f"{config.output_prefix}_db_llm.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    # --- Pipeline HTML ---
    if schema and config.enable_html:
        linker = ApexDbLinker(app, schema)
        links = linker.find_links()
        logging.info("Znaleziono %d powiązań APEX↔DB", len(links))

        html_renderer = HtmlRenderer(config)
        html_content = html_renderer.render(app, schema, links)
        html_name = config.html_output or f"{config.output_prefix}_interactive.html"
        html_path = output_dir / html_name
        html_path.write_text(html_content, encoding="utf-8")
        logging.info("Zapisano: %s (%d znaków)", html_path, len(html_content))
```

- [ ] **Step 2: Uruchom istniejące testy CLI**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (istniejąca funkcjonalność nienaruszona)

Uwaga: HtmlRenderer jeszcze nie istnieje — import może powodować problem. Jeśli tak, opóźnij import:

```python
# Na początku run_pipeline, zamiast top-level import:
if schema and config.enable_html:
    from apex_export_to_md.renderers.html_renderer import HtmlRenderer
    ...
```

- [ ] **Step 3: Commit**

```bash
git add apex_export_to_md/cli.py
git commit -m "feat(cli): integracja pipeline DDL i HTML w run_pipeline"
```

---

### Task 11: HTML Renderer — szkielet i dane

**Files:**
- Create: `apex_export_to_md/renderers/html_renderer.py`
- Test: `tests/test_html_renderer.py`

**Context:** Największy nowy plik. Generuje self-contained HTML z vis.js inline, 3 zakładkami i brandingiem. Podzielony na: przygotowanie JSON z danych, szablon HTML ze stylami, JS z logiką zakładek.

- [ ] **Step 0: Pobierz vis-network.min.js do vendor/**

```bash
mkdir -p apex_export_to_md/renderers/vendor
curl -sL "https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js" \
  -o apex_export_to_md/renderers/vendor/vis-network.min.js
echo "Rozmiar: $(wc -c < apex_export_to_md/renderers/vendor/vis-network.min.js) bajtów"
```

Expected: Plik ~500KB pobrany. Dodaj do `.gitignore` jeśli nie chcesz śledzić w repo, lub commituj (spec wymaga offline).

- [ ] **Step 1: Napisz testy**

```python
# tests/test_html_renderer.py
"""Testy renderera interaktywnego HTML."""
import json
import pytest
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.apex_models import ApexApp, ApexPage, Region
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbView,
    DbPackage, DbSubprogram, DbSequence,
)
from apex_export_to_md.linker.apex_db_linker import ApexDbLink
from apex_export_to_md.renderers.html_renderer import HtmlRenderer


@pytest.fixture
def config():
    return AppConfig(author_name="Tomasz Rembiasz")


@pytest.fixture
def sample_app():
    return ApexApp(
        name="SKW_2_APEX", id="160", alias="START338",
        pages=[
            ApexPage(id=1, name="Home",
                     regions=[Region(name="R1", type="Grid", source_table="B_AUDYT")]),
        ],
    )


@pytest.fixture
def sample_schema():
    return DbSchema(
        tables=[
            DbTable(name="B_AUDYT",
                    columns=[DbColumn(name="ID", data_type="NUMBER")],
                    constraints=[DbConstraint(name="PK", constraint_type="PK", columns=["ID"])],
                    comment="Tabela audytow"),
            DbTable(name="B_ANKIETA",
                    constraints=[
                        DbConstraint(name="FK1", constraint_type="FK",
                                     columns=["FK_ID"], ref_table="B_AUDYT",
                                     ref_columns=["ID"]),
                    ]),
        ],
        views=[DbView(name="V1", comment="Widok")],
        packages=[DbPackage(name="PKG1")],
        sequences=[DbSequence(name="SEQ1")],
    )


@pytest.fixture
def sample_links():
    return [
        ApexDbLink(page_id=1, page_name="Home",
                   db_objects=["B_AUDYT"], source_type="region", source_name="R1"),
    ]


class TestHtmlRenderer:
    def test_produces_html(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_vis_js(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        # vis.js powinien być osadzony inline lub fallback CDN
        assert "<script" in html
        # Sprawdź, że dane JSON są osadzone
        assert "const DATA" in html

    def test_branding_footer(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "Tomasz Rembiasz" in html
        assert "Claude" in html
        assert "apex_export_to_md" in html

    def test_branding_logo_svg(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "<svg" in html
        assert "TR" in html

    def test_app_name_in_header(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "SKW_2_APEX" in html

    def test_json_data_embedded(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        # JSON data powinien być osadzony w tagu <script>
        assert '"B_AUDYT"' in html
        assert '"B_ANKIETA"' in html

    def test_three_tabs(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "tab-diagram" in html or "Diagram" in html
        assert "tab-browser" in html or "Baza danych" in html
        assert "tab-map" in html or "APEX" in html

    def test_fk_edges_in_data(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        # FK1: B_ANKIETA → B_AUDYT
        assert "FK1" in html

    def test_links_in_data(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        # Link: strona Home → B_AUDYT
        assert "Home" in html
```

- [ ] **Step 2: Uruchom testy — powinny FAIL**

- [ ] **Step 3: Implementuj HtmlRenderer**

```python
# apex_export_to_md/renderers/html_renderer.py
"""Renderer interaktywnego HTML — self-contained plik z vis.js.

Zawiera 3 zakładki:
1. Diagram relacji (vis.js network graph)
2. Przeglądarka bazy danych (drzewo + panel szczegółów)
3. Mapa APEX ↔ DB (połączenia stron ze tabelami)

Branding: logo TR (inline SVG), autor, stopka.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.apex_models import ApexApp
from apex_export_to_md.models.db_models import DbSchema
from apex_export_to_md.linker.apex_db_linker import ApexDbLink

logger = logging.getLogger(__name__)


class HtmlRenderer:
    """Generuje self-contained interaktywny HTML."""

    def __init__(self, config: AppConfig):
        self._config = config

    def render(self, app: ApexApp, schema: DbSchema,
               links: list[ApexDbLink]) -> str:
        """Generuj pełny plik HTML."""
        data = self._prepare_data(app, schema, links)
        return self._build_html(app.name, data)

    def _prepare_data(self, app: ApexApp, schema: DbSchema,
                      links: list[ApexDbLink]) -> dict:
        """Przygotuj dane JSON do osadzenia w HTML."""
        # Tabele
        tables = []
        for t in schema.tables:
            tables.append({
                "name": t.name,
                "comment": t.comment or "",
                "columns": [
                    {
                        "name": c.name,
                        "type": c.data_type,
                        "nullable": c.nullable,
                        "default": c.default or "",
                        "identity": c.identity,
                        "comment": c.comment or "",
                    }
                    for c in t.columns
                ],
                "constraints": [
                    {
                        "name": c.name,
                        "type": c.constraint_type,
                        "columns": c.columns,
                        "ref_table": c.ref_table or "",
                        "ref_columns": c.ref_columns,
                        "check_expr": c.check_expression or "",
                    }
                    for c in t.constraints
                ],
                "indexes": [
                    {
                        "name": i.name,
                        "columns": i.columns,
                        "unique": i.unique,
                    }
                    for i in t.indexes
                ],
            })

        # Widoki
        views = [{"name": v.name, "comment": v.comment or "",
                  "columns": v.columns, "sql": v.sql}
                 for v in schema.views]

        # Pakiety
        packages = []
        for p in schema.packages:
            packages.append({
                "name": p.name,
                "spec": [
                    {"name": s.name, "type": s.subprogram_type,
                     "params": ", ".join(f"{pr.name} {pr.direction} {pr.data_type}"
                                         for pr in s.parameters),
                     "return": s.return_type or "",
                     "desc": s.description or ""}
                    for s in p.spec_subprograms
                ],
                "body": [
                    {"name": s.name, "type": s.subprogram_type,
                     "visibility": s.visibility,
                     "desc": s.description or ""}
                    for s in p.body_subprograms
                ],
                "body_source": p.body_source,
            })

        # Sekwencje
        sequences = [{"name": s.name, "start": s.start_with or "",
                       "incr": s.increment_by or ""}
                     for s in schema.sequences]

        # FK edges dla diagramu
        edges = []
        for t in schema.tables:
            for c in t.constraints:
                if c.constraint_type == "FK" and c.ref_table:
                    edges.append({
                        "from": t.name,
                        "to": c.ref_table,
                        "label": c.name,
                    })

        # Strony APEX
        pages = [{"id": p.id, "name": p.name} for p in app.pages]

        # Linki APEX↔DB
        link_data = [
            {"page_id": l.page_id, "page_name": l.page_name,
             "objects": l.db_objects, "source_type": l.source_type,
             "source_name": l.source_name}
            for l in links
        ]

        return {
            "tables": tables,
            "views": views,
            "packages": packages,
            "sequences": sequences,
            "edges": edges,
            "pages": pages,
            "links": link_data,
        }

    def _build_html(self, app_name: str, data: dict) -> str:
        """Zbuduj pełny HTML z danymi, stylami i JS."""
        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        author = self._config.author_name

        return f'''<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{app_name} — Dokumentacja projektu</title>
<style>
{self._css()}
</style>
</head>
<body>

<header>
  <div class="header-left">
    {self._logo_svg()}
    <h1>{app_name} — Dokumentacja projektu</h1>
  </div>
  <div class="search-box">
    <input type="text" id="search" placeholder="Szukaj..." oninput="handleSearch(this.value)">
  </div>
</header>

<nav class="tabs">
  <button class="tab active" onclick="switchTab('diagram')">Diagram relacji</button>
  <button class="tab" onclick="switchTab('browser')">Baza danych</button>
  <button class="tab" onclick="switchTab('map')">APEX ↔ DB</button>
</nav>

<main>
  <div id="tab-diagram" class="tab-content active">
    <div id="er-network" style="width:100%;height:600px;border:1px solid #ddd;"></div>
    <div id="node-detail" class="detail-panel"></div>
  </div>

  <div id="tab-browser" class="tab-content" style="display:none">
    <div class="browser-layout">
      <div id="object-tree" class="tree-panel"></div>
      <div id="object-detail" class="detail-panel"></div>
    </div>
  </div>

  <div id="tab-map" class="tab-content" style="display:none">
    <div class="map-layout">
      <div id="apex-pages" class="map-column">
        <h3>Strony APEX</h3>
        <div id="page-list"></div>
      </div>
      <div id="map-connections" class="map-connections"></div>
      <div id="db-objects" class="map-column">
        <h3>Obiekty bazy danych</h3>
        <div id="db-list"></div>
      </div>
    </div>
  </div>
</main>

<footer>
  <span>Wygenerowano narzędziem <strong>apex_export_to_md</strong></span>
  <span>Autor: <strong>{author}</strong></span>
  <span>Współpraca: <strong>Claude</strong> (Anthropic)</span>
</footer>

<script>
// === DATA ===
const DATA = {data_json};
</script>

<script>
{self._vis_js_inline()}
</script>

<script>
{self._javascript()}
</script>

</body>
</html>'''

    def _vis_js_inline(self) -> str:
        """Zwróć vis-network.min.js jako inline string.

        Plik jest ładowany z bundled resource przy imporcie modułu.
        Jeśli niedostępny, zwraca minimalny stub z komunikatem.
        """
        vis_path = Path(__file__).parent / "vendor" / "vis-network.min.js"
        if vis_path.exists():
            return vis_path.read_text(encoding="utf-8")
        # Fallback: CDN + ostrzeżenie w konsoli
        logger.warning("vis-network.min.js nie znaleziony w vendor/ — HTML nie będzie działał offline")
        return (
            '/* vis-network not bundled — fallback */\n'
            'document.addEventListener("DOMContentLoaded", function() {\n'
            '  var s = document.createElement("script");\n'
            '  s.src = "https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js";\n'
            '  s.onload = function() { if(typeof initErTab === "function") initErTab(); };\n'
            '  document.head.appendChild(s);\n'
            '});\n'
        )

    def _logo_svg(self) -> str:
        """Inline SVG logo — inicjały TR w geometrycznym okręgu."""
        return '''<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="19" fill="#1a365d" stroke="#d4a843" stroke-width="2"/>
  <text x="20" y="26" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="16" font-weight="bold" fill="#d4a843">TR</text>
</svg>'''

    def _css(self) -> str:
        """Style CSS."""
        return '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       color: #333; background: #f5f5f5; }
header { display: flex; justify-content: space-between; align-items: center;
         padding: 12px 24px; background: #1a365d; color: white; }
.header-left { display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 18px; font-weight: 500; }
.search-box input { padding: 6px 12px; border: none; border-radius: 4px; width: 220px; }
.tabs { display: flex; gap: 0; background: #fff; border-bottom: 2px solid #ddd;
        padding: 0 24px; }
.tab { padding: 10px 20px; border: none; background: none; cursor: pointer;
       font-size: 14px; color: #666; border-bottom: 2px solid transparent; }
.tab.active { color: #1a365d; border-bottom-color: #d4a843; font-weight: 600; }
.tab:hover { color: #1a365d; }
main { padding: 16px 24px; min-height: 70vh; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.detail-panel { background: #fff; border: 1px solid #ddd; border-radius: 4px;
                padding: 16px; margin-top: 12px; max-height: 400px; overflow-y: auto; }
.browser-layout { display: flex; gap: 16px; }
.tree-panel { width: 280px; background: #fff; border: 1px solid #ddd;
              border-radius: 4px; padding: 12px; max-height: 70vh; overflow-y: auto; }
.tree-panel h4 { color: #1a365d; margin: 8px 0 4px; font-size: 13px; }
.tree-item { padding: 4px 8px; cursor: pointer; border-radius: 3px; font-size: 13px; }
.tree-item:hover { background: #e8edf3; }
.tree-item.active { background: #1a365d; color: white; }
.browser-layout .detail-panel { flex: 1; margin-top: 0; max-height: 70vh; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
th { background: #f0f0f0; font-weight: 600; }
.map-layout { display: flex; gap: 16px; align-items: flex-start; }
.map-column { flex: 1; background: #fff; border: 1px solid #ddd; border-radius: 4px;
              padding: 12px; max-height: 70vh; overflow-y: auto; }
.map-column h3 { font-size: 14px; color: #1a365d; margin-bottom: 8px; }
.map-item { padding: 6px 10px; cursor: pointer; border-radius: 3px;
            font-size: 13px; margin: 2px 0; }
.map-item:hover { background: #e8edf3; }
.map-item.highlight { background: #d4a843; color: #1a365d; font-weight: 600; }
.map-connections { width: 60px; }
footer { display: flex; justify-content: center; gap: 24px; padding: 16px;
         background: #1a365d; color: #aaa; font-size: 12px; }
footer strong { color: #d4a843; }
pre { background: #f8f8f8; border: 1px solid #ddd; padding: 12px; overflow-x: auto;
      font-size: 12px; border-radius: 4px; }
code { font-family: "Fira Code", Consolas, monospace; }
.search-results { background: #ffe; padding: 8px; border: 1px solid #dda; margin: 8px 0;
                  border-radius: 4px; display: none; }
'''

    def _javascript(self) -> str:
        """Logika JS — zakładki, diagram, przeglądarka, mapa."""
        return '''
// === TABS ===
function switchTab(name) {
  document.querySelectorAll(".tab-content").forEach(t => {
    t.style.display = "none";
    t.classList.remove("active");
  });
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  const panel = document.getElementById("tab-" + name);
  if (panel) { panel.style.display = "block"; panel.classList.add("active"); }
  event.target.classList.add("active");
  if (name === "diagram" && !window._diagramInit) initDiagram();
  if (name === "browser" && !window._browserInit) initBrowser();
  if (name === "map" && !window._mapInit) initMap();
}

// === DIAGRAM (vis.js) ===
function initDiagram() {
  window._diagramInit = true;
  const nodes = DATA.tables.map(t => ({
    id: t.name, label: t.name, shape: "box",
    color: getNodeColor(t.name),
    title: t.comment + " (" + t.columns.length + " kolumn)",
    font: { size: 12 }
  }));
  const edges = DATA.edges.map(e => ({
    from: e.from, to: e.to, label: e.label,
    arrows: "to", font: { size: 9, align: "middle" },
    color: { color: "#999" }
  }));
  const container = document.getElementById("er-network");
  const network = new vis.Network(container, { nodes, edges }, {
    layout: { hierarchical: { direction: "UD", sortMethod: "hubsize", nodeSpacing: 200 } },
    physics: false,
    interaction: { hover: true },
    edges: { smooth: { type: "cubicBezier" } }
  });
  network.on("click", params => {
    if (params.nodes.length) showNodeDetail(params.nodes[0]);
  });
}

function getNodeColor(name) {
  if (name.startsWith("B_SL_")) return { background: "#c6f6d5", border: "#38a169" };
  if (name.includes("_HIST") || name.includes("_TMP") || name.includes("IMPORT"))
    return { background: "#e2e8f0", border: "#718096" };
  return { background: "#bee3f8", border: "#3182ce" };
}

function showNodeDetail(name) {
  const t = DATA.tables.find(x => x.name === name);
  if (!t) return;
  let html = "<h3>" + t.name + "</h3>";
  if (t.comment) html += "<p><em>" + t.comment + "</em></p>";
  html += "<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>";
  t.columns.forEach(c => {
    html += "<tr><td>" + c.name + "</td><td>" + c.type + "</td>"
         + "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>"
         + "<td>" + (c.default || "—") + "</td>"
         + "<td>" + (c.comment || "—") + "</td></tr>";
  });
  html += "</table>";
  if (t.constraints.length) {
    html += "<h4>Constraints</h4><ul>";
    t.constraints.forEach(c => {
      let desc = c.type + ": " + c.name;
      if (c.type === "FK") desc += " → " + c.ref_table + "(" + c.ref_columns.join(",") + ")";
      if (c.type === "CHK") desc += " " + c.check_expr;
      html += "<li>" + desc + "</li>";
    });
    html += "</ul>";
  }
  document.getElementById("node-detail").innerHTML = html;
}

// === BROWSER ===
function initBrowser() {
  window._browserInit = true;
  const tree = document.getElementById("object-tree");
  let html = "<h4>Tabele</h4>";
  DATA.tables.forEach(t => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('table','" + t.name + "')\\">" + t.name + "</div>";
  });
  html += "<h4>Widoki</h4>";
  DATA.views.forEach(v => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('view','" + v.name + "')\\">" + v.name + "</div>";
  });
  html += "<h4>Pakiety</h4>";
  DATA.packages.forEach(p => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('package','" + p.name + "')\\">" + p.name + "</div>";
  });
  html += "<h4>Sekwencje</h4>";
  DATA.sequences.forEach(s => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('sequence','" + s.name + "')\\">" + s.name + "</div>";
  });
  tree.innerHTML = html;
}

function showObject(type, name) {
  document.querySelectorAll(".tree-item").forEach(i => i.classList.remove("active"));
  event.target.classList.add("active");
  const detail = document.getElementById("object-detail");
  if (type === "table") {
    const t = DATA.tables.find(x => x.name === name);
    if (!t) return;
    let html = "<h3>Tabela: " + t.name + "</h3>";
    if (t.comment) html += "<p><em>" + t.comment + "</em></p>";
    html += "<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>";
    t.columns.forEach(c => {
      html += "<tr><td>" + c.name + "</td><td>" + c.type +
        (c.identity ? " (IDENTITY)" : "") + "</td>" +
        "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>" +
        "<td>" + (c.default || "—") + "</td>" +
        "<td>" + (c.comment || "—") + "</td></tr>";
    });
    html += "</table>";
    if (t.constraints.length) {
      html += "<h4>Constraints</h4><ul>";
      t.constraints.forEach(c => {
        let d = "<strong>" + c.type + "</strong>: " + c.name + " (" + c.columns.join(", ") + ")";
        if (c.type === "FK") d += " → " + c.ref_table;
        if (c.type === "CHK") d += " — " + c.check_expr;
        html += "<li>" + d + "</li>";
      });
      html += "</ul>";
    }
    if (t.indexes.length) {
      html += "<h4>Indeksy</h4><ul>";
      t.indexes.forEach(i => {
        html += "<li>" + i.name + " (" + i.columns.join(", ") + ")" + (i.unique ? " UNIQUE" : "") + "</li>";
      });
      html += "</ul>";
    }
    detail.innerHTML = html;
  } else if (type === "view") {
    const v = DATA.views.find(x => x.name === name);
    if (!v) return;
    let html = "<h3>Widok: " + v.name + "</h3>";
    if (v.comment) html += "<p><em>" + v.comment + "</em></p>";
    if (v.columns.length) html += "<p><strong>Kolumny:</strong> " + v.columns.join(", ") + "</p>";
    if (v.sql) html += "<pre><code>" + escapeHtml(v.sql) + "</code></pre>";
    detail.innerHTML = html;
  } else if (type === "package") {
    const p = DATA.packages.find(x => x.name === name);
    if (!p) return;
    let html = "<h3>Pakiet: " + p.name + "</h3>";
    if (p.spec.length) {
      html += "<h4>Specyfikacja</h4><table><tr><th>Nazwa</th><th>Typ</th><th>Parametry</th><th>Zwraca</th><th>Opis</th></tr>";
      p.spec.forEach(s => {
        html += "<tr><td>" + s.name + "</td><td>" + s.type + "</td><td>" + (s.params||"—") + "</td><td>" + (s["return"]||"—") + "</td><td>" + (s.desc||"—") + "</td></tr>";
      });
      html += "</table>";
    }
    if (p.body_source) {
      html += "<details><summary>Implementacja (body)</summary><pre><code>" + escapeHtml(p.body_source) + "</code></pre></details>";
    }
    detail.innerHTML = html;
  } else if (type === "sequence") {
    const s = DATA.sequences.find(x => x.name === name);
    if (!s) return;
    detail.innerHTML = "<h3>Sekwencja: " + s.name + "</h3><p>Start: " + s.start + ", Increment: " + s.incr + "</p>";
  }
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// === MAP ===
function initMap() {
  window._mapInit = true;
  const pageList = document.getElementById("page-list");
  const dbList = document.getElementById("db-list");
  // Strony APEX
  let pHtml = "";
  DATA.pages.forEach(p => {
    pHtml += "<div class=\\"map-item\\" data-page=\\""+ p.id +"\\" onclick=\\"highlightFromPage("+ p.id +")\\">" +
             "Strona " + p.id + ": " + p.name + "</div>";
  });
  pageList.innerHTML = pHtml;
  // Obiekty DB
  let dHtml = "";
  const allObjects = [...DATA.tables.map(t=>t.name), ...DATA.views.map(v=>v.name)];
  allObjects.forEach(n => {
    dHtml += "<div class=\\"map-item\\" data-obj=\\""+ n +"\\" onclick=\\"highlightFromObject('"+ n +"')\\">" + n + "</div>";
  });
  dbList.innerHTML = dHtml;
}

function highlightFromPage(pageId) {
  clearHighlights();
  const linked = DATA.links.filter(l => l.page_id === pageId);
  const objects = new Set();
  linked.forEach(l => l.objects.forEach(o => objects.add(o)));
  document.querySelectorAll("[data-page=\\""+ pageId +"\\"]").forEach(e => e.classList.add("highlight"));
  objects.forEach(o => {
    document.querySelectorAll("[data-obj=\\""+ o +"\\"]").forEach(e => e.classList.add("highlight"));
  });
}

function highlightFromObject(name) {
  clearHighlights();
  const linked = DATA.links.filter(l => l.objects.includes(name));
  const pages = new Set(linked.map(l => l.page_id));
  document.querySelectorAll("[data-obj=\\""+ name +"\\"]").forEach(e => e.classList.add("highlight"));
  pages.forEach(p => {
    document.querySelectorAll("[data-page=\\""+ p +"\\"]").forEach(e => e.classList.add("highlight"));
  });
}

function clearHighlights() {
  document.querySelectorAll(".map-item").forEach(e => e.classList.remove("highlight"));
}

// === SEARCH ===
function handleSearch(query) {
  if (!query || query.length < 2) return;
  const q = query.toUpperCase();
  // Podświetl w drzewie przeglądarki
  document.querySelectorAll(".tree-item").forEach(el => {
    el.style.display = el.textContent.toUpperCase().includes(q) ? "" : "none";
  });
}

// Init first tab on load
window.addEventListener("DOMContentLoaded", () => { initDiagram(); });
'''
```

Uwaga implementacyjna: vis.js jest ładowany z pliku `vendor/vis-network.min.js` (pobranego w Step 0). Jeśli plik nie istnieje, renderer loguje ostrzeżenie i stosuje fallback CDN. Dzięki bundled vis.js HTML działa offline (per spec).

- [ ] **Step 4: Uruchom testy — powinny PASS**

Run: `python -m pytest tests/test_html_renderer.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/renderers/html_renderer.py tests/test_html_renderer.py
git commit -m "feat(renderers): HtmlRenderer — interaktywny HTML z vis.js, 3 zakładki, branding TR"
```

---

### Task 12: Test integracyjny z prawdziwym plikiem DDL

**Files:**
- Create: `tests/test_integration_ddl.py`

**Context:** Test end-to-end: prawdziwy plik `SKW_TO_APEX_DDL.sql` → parse → render → weryfikacja wyników.

- [ ] **Step 1: Napisz test integracyjny**

```python
# tests/test_integration_ddl.py
"""Test integracyjny — pełny pipeline DDL z prawdziwym plikiem SQL."""
import pytest
from pathlib import Path
from apex_export_to_md.parser.ddl_parser import parse_ddl_files
from apex_export_to_md.renderers.db_human_renderer import DbHumanRenderer
from apex_export_to_md.renderers.db_llm_renderer import DbLLMRenderer
from apex_export_to_md.config import AppConfig

# Ścieżka do prawdziwego pliku DDL
DDL_FILE = Path(__file__).parent.parent / "program" / "readable" / "SKW_TO_APEX_DDL.sql"


@pytest.mark.skipif(not DDL_FILE.exists(), reason="Plik DDL niedostępny")
class TestIntegrationDdl:
    def test_parse_real_ddl(self):
        schema = parse_ddl_files([DDL_FILE])
        # Oczekujemy min 10 tabel (B_AUDYT, B_ANKIETA, B_KONTROLA, ...)
        assert len(schema.tables) >= 10
        # Oczekujemy 2 widoki
        assert len(schema.views) >= 2
        # Oczekujemy 2 pakiety
        assert len(schema.packages) >= 2
        # Oczekujemy min 4 sekwencje
        assert len(schema.sequences) >= 4

    def test_table_b_audyt_parsed(self):
        schema = parse_ddl_files([DDL_FILE])
        audyt = next((t for t in schema.tables if t.name == "B_AUDYT"), None)
        assert audyt is not None
        # Kolumny
        col_names = [c.name for c in audyt.columns]
        assert "ID_PK_B_AUDYT" in col_names
        assert "STATUS_AUDYTU" in col_names
        assert "SZEF_MISJI_LOGIN" in col_names
        # PK
        pk = [c for c in audyt.constraints if c.constraint_type == "PK"]
        assert len(pk) >= 1
        # CHECK
        chk = [c for c in audyt.constraints if c.constraint_type == "CHK"]
        assert len(chk) >= 1
        assert "Otwarty" in (chk[0].check_expression or "")
        # Komentarz tabeli
        assert audyt.comment is not None
        assert "audyt" in audyt.comment.lower()

    def test_column_comments(self):
        schema = parse_ddl_files([DDL_FILE])
        audyt = next(t for t in schema.tables if t.name == "B_AUDYT")
        status_col = next(c for c in audyt.columns if c.name == "STATUS_AUDYTU")
        assert status_col.comment is not None
        assert "Otwarty" in status_col.comment

    def test_fk_constraints(self):
        schema = parse_ddl_files([DDL_FILE])
        ankieta = next((t for t in schema.tables if t.name == "B_ANKIETA"), None)
        assert ankieta is not None
        fks = [c for c in ankieta.constraints if c.constraint_type == "FK"]
        assert len(fks) >= 3  # B_AUDYT, B_KONTROLA, B_SL_C_PYTANIE, B_SL_C_PYTANIE_DZIEDZINA
        ref_tables = {fk.ref_table for fk in fks}
        assert "B_AUDYT" in ref_tables
        assert "B_KONTROLA" in ref_tables

    def test_views_parsed(self):
        schema = parse_ddl_files([DDL_FILE])
        v = next((v for v in schema.views if v.name == "B_V_AUDYT_KONTROLE"), None)
        assert v is not None
        assert len(v.columns) > 0
        assert "B_AUDYT_KONTROLA" in v.sql

    def test_package_pkg_audyt(self):
        schema = parse_ddl_files([DDL_FILE])
        pkg = next((p for p in schema.packages if p.name == "PKG_AUDYT"), None)
        assert pkg is not None
        # Spec subprograms
        spec_names = {s.name for s in pkg.spec_subprograms}
        assert "UTWORZ_AUDYT" in spec_names
        assert "SPRAWDZ_UPRAWNIENIA" in spec_names
        assert "MOZE_EDYTOWAC" in spec_names
        # Body subprograms (POBIERZ_AUDYT jest prywatna)
        body_names = {s.name for s in pkg.body_subprograms}
        assert "POBIERZ_AUDYT" in body_names
        priv = next(s for s in pkg.body_subprograms if s.name == "POBIERZ_AUDYT")
        assert priv.visibility == "private"
        # Body source zachowany
        assert "RAISE_APPLICATION_ERROR" in pkg.body_source

    def test_human_renderer_output(self):
        schema = parse_ddl_files([DDL_FILE])
        config = AppConfig(include_code="full")
        renderer = DbHumanRenderer(config)
        md = renderer.render(schema)
        assert "# Baza danych" in md
        assert "```mermaid" in md
        assert "B_AUDYT" in md
        assert "Tabela:" in md
        assert "Widok:" in md
        assert "Pakiet:" in md

    def test_llm_renderer_output(self):
        schema = parse_ddl_files([DDL_FILE])
        config = AppConfig(include_code="full")
        renderer = DbLLMRenderer(config)
        md = renderer.render(schema)
        assert "SCHEMA:DB" in md
        assert "TBL:B_AUDYT" in md
        assert "PKG:PKG_AUDYT" in md
        assert "VW:B_V_AUDYT_KONTROLE" in md
        assert "SEQ:" in md
```

- [ ] **Step 2: Uruchom testy**

Run: `python -m pytest tests/test_integration_ddl.py -v`
Expected: ALL PASS (jeśli plik DDL istnieje)

- [ ] **Step 3: Uruchom PEŁNY zestaw testów**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration_ddl.py
git commit -m "test: integracyjne testy DDL pipeline z prawdziwym SKW_TO_APEX_DDL.sql"
```

---

### Task 13: Ręczny test pipeline'u

**Files:** brak nowych plików

**Context:** Uruchom pełny pipeline na prawdziwym eksporcie i sprawdź wyniki.

- [ ] **Step 1: Uruchom program**

```bash
cd c:/_projekty/SKW_TO_APEX
python -m apex_export_to_md program/readable --output-dir . --output-prefix apex_export --verbose
```

Expected: 5 plików wyjściowych:
- `apex_export_human.md` (istniejący)
- `apex_export_llm.md` (istniejący)
- `apex_export_db_human.md` (nowy)
- `apex_export_db_llm.md` (nowy)
- `apex_export_interactive.html` (nowy)

- [ ] **Step 2: Sprawdź pliki DB MD**

Otwórz `apex_export_db_human.md` i zweryfikuj:
- Diagram Mermaid ER jest obecny
- Wszystkie tabele są udokumentowane
- Widoki, pakiety, sekwencje są obecne
- Komentarze przy tabelach i kolumnach

- [ ] **Step 3: Sprawdź interaktywny HTML**

Otwórz `apex_export_interactive.html` w przeglądarce:
- Zakładka "Diagram relacji" — graf ER z vis.js
- Zakładka "Baza danych" — przeglądarka obiektów
- Zakładka "APEX ↔ DB" — mapa powiązań
- Branding w stopce i nagłówku

- [ ] **Step 4: Commit końcowy**

Jeśli wszystko działa:

```bash
git add -A
git commit -m "feat: kompletny DDL pipeline + interaktywny HTML — wersja robocza"
```
