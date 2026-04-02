# DDL Pipeline Enhancements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend DDL pipeline with 7 enhancements: error codes extraction, NOCACHE/cache rendering, package constants & body params in HTML, UQ names in LLM, and APEX→package/dynamic-action linking.

**Architecture:** Changes touch 4 layers: model (`db_models.py`), parser (`ddl_parser.py`), renderers (3 files), linker (`apex_db_linker.py`). Each enhancement is self-contained. TDD approach.

**Tech Stack:** Python 3.12, pytest, dataclasses, regex

---

### Task 1: Error codes extraction — model + parser

**Files:**
- Modify: `apex_export_to_md/models/db_models.py` (DbPackage class)
- Modify: `apex_export_to_md/parser/ddl_parser.py` (parse_package function)
- Test: `tests/test_ddl_parser.py`

- [ ] **Step 1: Write failing test for error_codes field**

```python
# W tests/test_ddl_parser.py — nowa klasa na końcu pliku

class TestErrorCodesExtraction:
    def test_error_codes_extracted_from_body(self):
        sql = '''create or replace PACKAGE BODY PKG_TEST AS
            PROCEDURE P1(p_id NUMBER) IS
            BEGIN
                RAISE_APPLICATION_ERROR(-20001,
                    'Audyt nie istnieje.');
                RAISE_APPLICATION_ERROR(-20010,
                    'Nie mozna dodac kontroli.');
            END P1;
        END PKG_TEST;'''
        pkg = parse_package(sql)
        assert pkg is not None
        assert len(pkg.error_codes) == 2
        assert pkg.error_codes[0] == (-20001, "Audyt nie istnieje.")
        assert pkg.error_codes[1] == (-20010, "Nie mozna dodac kontroli.")

    def test_error_codes_empty_for_spec(self):
        sql = '''create or replace PACKAGE PKG_TEST AS
            PROCEDURE P1(p_id NUMBER);
        END PKG_TEST;'''
        pkg = parse_package(sql)
        assert pkg is not None
        assert pkg.error_codes == []

    def test_error_codes_with_concatenation(self):
        """Kody z dynamicznym tekstem — wyciągamy tylko statyczną część."""
        sql = """create or replace PACKAGE BODY PKG_T AS
            PROCEDURE P1 IS
            BEGIN
                RAISE_APPLICATION_ERROR(-20001,
                    'Audyt o ID=' || p_id || ' nie istnieje.');
            END P1;
        END PKG_T;"""
        pkg = parse_package(sql)
        assert len(pkg.error_codes) == 1
        assert pkg.error_codes[0][0] == -20001
        assert pkg.error_codes[0][1] == "Audyt o ID="

    def test_error_codes_multiline_string(self):
        """RAISE z tekstem rozbitym na wiele linii z konkatenacją."""
        sql = """create or replace PACKAGE BODY PKG_T AS
            PROCEDURE P1 IS
            BEGIN
                RAISE_APPLICATION_ERROR(-20030,
                    'Tylko szef misji moze zamrozic audyt. ' ||
                    'Status: ' || v_status);
            END P1;
        END PKG_T;"""
        pkg = parse_package(sql)
        assert len(pkg.error_codes) == 1
        assert pkg.error_codes[0][0] == -20030
        assert pkg.error_codes[0][1] == "Tylko szef misji moze zamrozic audyt. "
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ddl_parser.py::TestErrorCodesExtraction -v`
Expected: FAIL — `DbPackage` has no `error_codes` attribute

- [ ] **Step 3: Add error_codes field to DbPackage model**

In `apex_export_to_md/models/db_models.py`, add to `DbPackage`:
```python
error_codes: list[tuple[int, str]] = field(default_factory=list)  # (kod, tekst) z RAISE_APPLICATION_ERROR
```

- [ ] **Step 4: Add _extract_error_codes helper and call it in parse_package**

In `apex_export_to_md/parser/ddl_parser.py`, add helper function before `parse_package`:
```python
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
    return sorted(unique, key=lambda x: x[0])
```

In `parse_package`, after `pkg.body_source = source`, add:
```python
        pkg.error_codes = _extract_error_codes(source)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_ddl_parser.py::TestErrorCodesExtraction -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apex_export_to_md/models/db_models.py apex_export_to_md/parser/ddl_parser.py tests/test_ddl_parser.py
git commit -m "feat(parser): ekstrakcja kodów błędów RAISE_APPLICATION_ERROR z body PL/SQL"
```

---

### Task 2: Error codes rendering — all 3 renderers

**Files:**
- Modify: `apex_export_to_md/renderers/db_human_renderer.py`
- Modify: `apex_export_to_md/renderers/db_llm_renderer.py`
- Modify: `apex_export_to_md/renderers/html_renderer.py`
- Test: `tests/test_db_human_renderer.py`, `tests/test_db_llm_renderer.py`, `tests/test_html_renderer.py`

- [ ] **Step 1: Write failing tests for error codes in all renderers**

In `tests/test_db_human_renderer.py`, add method to class `TestDbHumanRenderer`:
```python
def test_error_codes_rendered(self, config, sample_schema):
    # Dodaj error_codes do pakietu w sample_schema
    sample_schema.packages[0].error_codes = [
        (-20001, "Audyt nie istnieje."),
        (-20010, "Nie mozna dodac kontroli."),
    ]
    renderer = DbHumanRenderer(config)
    result = renderer.render(sample_schema)
    assert "Kody błędów" in result
    assert "-20001" in result
    assert "Audyt nie istnieje." in result
    assert "-20010" in result
```

In `tests/test_db_llm_renderer.py`, add method to class `TestDbLLMRenderer`:
```python
def test_error_codes_rendered(self, config, sample_schema):
    sample_schema.packages[0].error_codes = [
        (-20001, "Audyt nie istnieje."),
    ]
    renderer = DbLLMRenderer(config)
    result = renderer.render(sample_schema)
    assert "ERR:-20001" in result
    assert "Audyt nie istnieje." in result
```

In `tests/test_html_renderer.py`, add method to class `TestHtmlRenderer`:
```python
def test_error_codes_in_html_data(self, config, sample_schema, sample_app, sample_links):
    sample_schema.packages[0].error_codes = [(-20001, "Test error")]
    renderer = HtmlRenderer(config)
    html = renderer.render(sample_app, sample_schema, sample_links)
    assert "-20001" in html
    assert "Test error" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_db_human_renderer.py::test_error_codes_rendered tests/test_db_llm_renderer.py::test_error_codes_rendered tests/test_html_renderer.py::test_error_codes_in_html_data -v`
Expected: FAIL

- [ ] **Step 3: Add error codes to DbHumanRenderer**

In `db_human_renderer.py`, in `_render_package`, after the private subprograms section (after line 216) and before the body_source block, add:
```python
        if pkg.error_codes:
            lines.append("#### Kody błędów")
            lines.append("")
            lines.append("| Kod | Opis |")
            lines.append("|-----|------|")
            for code, text in pkg.error_codes:
                lines.append(f"| {code} | {text} |")
            lines.append("")
```

- [ ] **Step 4: Add error codes to DbLLMRenderer**

In `db_llm_renderer.py`, in `_render_package`, after constants loop (after line 113) and before body_source, add:
```python
        for code, text in pkg.error_codes:
            lines.append(f"  ERR:{code}|{text}")
```

- [ ] **Step 5: Add error codes to HtmlRenderer**

In `html_renderer.py`, in `_prepare_data`, in the packages dict (after `"body_source": p.body_source` at line 100), add:
```python
                "error_codes": [{"code": c, "text": t} for c, t in p.error_codes],
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_db_human_renderer.py tests/test_db_llm_renderer.py tests/test_html_renderer.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apex_export_to_md/renderers/db_human_renderer.py apex_export_to_md/renderers/db_llm_renderer.py apex_export_to_md/renderers/html_renderer.py tests/test_db_human_renderer.py tests/test_db_llm_renderer.py tests/test_html_renderer.py
git commit -m "feat(renderers): renderowanie kodów błędów RAISE_APPLICATION_ERROR we wszystkich formatach"
```

---

### Task 3: NOCACHE on sequences — model + parser + renderers

**Files:**
- Modify: `apex_export_to_md/models/db_models.py`
- Modify: `apex_export_to_md/parser/ddl_parser.py`
- Modify: `apex_export_to_md/renderers/db_human_renderer.py`
- Modify: `apex_export_to_md/renderers/db_llm_renderer.py`
- Modify: `apex_export_to_md/renderers/html_renderer.py`
- Test: `tests/test_ddl_parser.py`, `tests/test_db_human_renderer.py`

- [ ] **Step 1: Write failing tests**

In `tests/test_ddl_parser.py`, add:
```python
class TestSequenceNocache:
    def test_nocache_detected(self):
        sql = 'CREATE SEQUENCE "SEQ1" MINVALUE 1 MAXVALUE 999 INCREMENT BY 1 START WITH 1 NOCACHE NOORDER NOCYCLE'
        seq = parse_create_sequence(sql)
        assert seq is not None
        assert seq.nocache is True
        assert seq.cache is None

    def test_cache_number(self):
        sql = 'CREATE SEQUENCE "SEQ2" MINVALUE 1 INCREMENT BY 1 CACHE 20'
        seq = parse_create_sequence(sql)
        assert seq.nocache is False
        assert seq.cache == "20"

    def test_no_cache_clause(self):
        sql = 'CREATE SEQUENCE "SEQ3" INCREMENT BY 1'
        seq = parse_create_sequence(sql)
        assert seq.nocache is False
        assert seq.cache is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ddl_parser.py::TestSequenceNocache -v`
Expected: FAIL — no `nocache` attribute

- [ ] **Step 3: Add nocache field and parse it**

In `db_models.py`, add to `DbSequence`:
```python
    nocache: bool = False
```

In `ddl_parser.py`, in `parse_create_sequence`, after the return statement construction, add nocache detection. Replace the return block:
```python
    return DbSequence(
        name=name,
        min_value=_extract(r'MINVALUE\s+(\d+)'),
        max_value=_extract(r'MAXVALUE\s+(\d+)'),
        increment_by=_extract(r'INCREMENT\s+BY\s+(\d+)'),
        start_with=_extract(r'START\s+WITH\s+(\d+)'),
        cache=_extract(r'CACHE\s+(\d+)'),
        nocache=bool(re.search(r'\bNOCACHE\b', sql, re.IGNORECASE)),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ddl_parser.py::TestSequenceNocache -v`
Expected: PASS

- [ ] **Step 5: Add Cache column to human renderer sequence table**

In `db_human_renderer.py`, replace the sequence rendering block (lines 50-58):
```python
            lines.append("| Nazwa | Start | Increment | Min | Max | Cache |")
            lines.append("|-------|-------|-----------|-----|-----|-------|")
            for seq in schema.sequences:
                cache = "NOCACHE" if seq.nocache else (seq.cache or "—")
                lines.append(
                    f"| {seq.name} | {seq.start_with or '—'} "
                    f"| {seq.increment_by or '—'} "
                    f"| {seq.min_value or '—'} "
                    f"| {seq.max_value or '—'} "
                    f"| {cache} |"
                )
```

- [ ] **Step 6: Add cache/nocache to LLM renderer**

In `db_llm_renderer.py`, in the sequence rendering loop (lines 31-36), after the `INCR` part, add:
```python
            if seq.nocache:
                parts.append("NOCACHE")
            elif seq.cache:
                parts.append(f"CACHE:{seq.cache}")
```

- [ ] **Step 7: Add cache/nocache to HTML renderer**

In `html_renderer.py`, replace sequence serialization (lines 104-106):
```python
        sequences = [{"name": s.name, "start": s.start_with or "",
                       "incr": s.increment_by or "",
                       "cache": "NOCACHE" if s.nocache else (s.cache or "")}
                     for s in schema.sequences]
```

- [ ] **Step 8: Add test for Cache column in human renderer**

In `tests/test_db_human_renderer.py`, add method to class `TestDbHumanRenderer`:
```python
def test_sequence_cache_rendered(self, config):
    schema = DbSchema(
        sequences=[
            DbSequence(name="SEQ1", start_with="1", increment_by="1", nocache=True),
            DbSequence(name="SEQ2", start_with="1", increment_by="1", cache="20"),
        ],
    )
    renderer = DbHumanRenderer(config)
    result = renderer.render(schema)
    assert "NOCACHE" in result
    assert "| Cache |" in result
```

Don't forget to add `DbSequence` to the import from `db_models` in this test file.

- [ ] **Step 9: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add apex_export_to_md/models/db_models.py apex_export_to_md/parser/ddl_parser.py apex_export_to_md/renderers/db_human_renderer.py apex_export_to_md/renderers/db_llm_renderer.py apex_export_to_md/renderers/html_renderer.py tests/test_ddl_parser.py tests/test_db_human_renderer.py
git commit -m "feat(parser+renderers): NOCACHE/CACHE na sekwencjach — parsowanie i renderowanie"
```

---

### Task 4: Package constants in HTML

**Files:**
- Modify: `apex_export_to_md/renderers/html_renderer.py`
- Test: `tests/test_html_renderer.py`

- [ ] **Step 1: Write failing test**

In `tests/test_html_renderer.py`, add method to class `TestHtmlRenderer`:
```python
def test_package_constants_in_html(self, config, sample_schema, sample_app, sample_links):
    sample_schema.packages[0].constants = ["C_STATUS_OTWARTY CONSTANT VARCHAR2(20) := 'Otwarty'"]
    renderer = HtmlRenderer(config)
    html = renderer.render(sample_app, sample_schema, sample_links)
    assert "C_STATUS_OTWARTY" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_html_renderer.py::TestHtmlRenderer::test_package_constants_in_html -v`
Expected: FAIL

- [ ] **Step 3: Add constants to packages JSON**

In `html_renderer.py`, in `_prepare_data`, in the packages dict, after `"body_source": p.body_source`, add:
```python
                "constants": p.constants,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_html_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/renderers/html_renderer.py tests/test_html_renderer.py
git commit -m "fix(html): dodanie stałych pakietów (constants) do danych JSON HTML"
```

---

### Task 5: Body subprogram parameters in HTML

**Files:**
- Modify: `apex_export_to_md/renderers/html_renderer.py`
- Test: `tests/test_html_renderer.py`

- [ ] **Step 1: Write failing test**

In `tests/test_html_renderer.py`, add method to class `TestHtmlRenderer`:
```python
def test_body_subprogram_params_in_html(self, config, sample_schema, sample_app, sample_links):
    from apex_export_to_md.models.db_models import DbSubprogram, DbParameter
    sample_schema.packages[0].body_subprograms = [
        DbSubprogram(
            name="PRIV_PROC", subprogram_type="PROCEDURE",
            visibility="private",
            parameters=[DbParameter(name="p_id", data_type="NUMBER", direction="IN")],
        )
    ]
    renderer = HtmlRenderer(config)
    html = renderer.render(sample_app, sample_schema, sample_links)
    # Parametry body subprogramów powinny być w HTML
    assert "p_id IN NUMBER" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_html_renderer.py::TestHtmlRenderer::test_body_subprogram_params_in_html -v`
Expected: FAIL

- [ ] **Step 3: Add params to body subprogram dict**

In `html_renderer.py`, replace the body subprogram dict (lines 94-99):
```python
                "body": [
                    {"name": s.name, "type": s.subprogram_type,
                     "visibility": s.visibility,
                     "params": ", ".join(f"{pr.name} {pr.direction} {pr.data_type}"
                                         for pr in s.parameters),
                     "return": s.return_type or "",
                     "desc": s.description or ""}
                    for s in p.body_subprograms
                ],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_html_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/renderers/html_renderer.py tests/test_html_renderer.py
git commit -m "fix(html): parametry i return_type dla body subprogramów w danych JSON HTML"
```

---

### Task 6: UQ constraint names in LLM renderer

**Files:**
- Modify: `apex_export_to_md/renderers/db_llm_renderer.py`
- Test: `tests/test_db_llm_renderer.py`

- [ ] **Step 1: Write failing test**

In `tests/test_db_llm_renderer.py`, add method to class `TestDbLLMRenderer`:
```python
def test_uq_constraint_name_rendered(self, config, sample_schema):
    from apex_export_to_md.models.db_models import DbConstraint
    sample_schema.tables[0].constraints.append(
        DbConstraint(name="UQ_STATUS", constraint_type="UQ", columns=["STATUS_AUDYTU"])
    )
    renderer = DbLLMRenderer(config)
    result = renderer.render(sample_schema)
    assert "UQ:UQ_STATUS|STATUS_AUDYTU" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db_llm_renderer.py::TestDbLLMRenderer::test_uq_constraint_name_rendered -v`
Expected: FAIL — currently renders `UQ:STATUS_AUDYTU` without name

- [ ] **Step 3: Add constraint name to UQ rendering**

In `db_llm_renderer.py`, replace line 73:
```python
                lines.append(f"  UQ:{c.name}|{cols}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db_llm_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/renderers/db_llm_renderer.py tests/test_db_llm_renderer.py
git commit -m "fix(llm-renderer): nazwa constraint w UQ — UQ:name|cols zamiast UQ:cols"
```

---

### Task 7: APEX → PL/SQL package linking + dynamic actions scanning

**Files:**
- Modify: `apex_export_to_md/linker/apex_db_linker.py`
- Test: `tests/test_apex_db_linker.py`

- [ ] **Step 1: Write failing tests for package linking**

In `tests/test_apex_db_linker.py`, make two changes:

**a)** Update the import on line 7 — add `DbPackage`:
```python
from apex_export_to_md.models.db_models import DbSchema, DbTable, DbView, DbPackage
```

**b)** Update the existing `db_schema` fixture (line 12) — add `packages` parameter while preserving existing tables and views:
```python
@pytest.fixture
def db_schema():
    return DbSchema(
        tables=[
            DbTable(name="B_AUDYT"),
            DbTable(name="B_AUDYT_KONTROLA"),
            DbTable(name="B_KONTROLA"),
        ],
        views=[DbView(name="B_V_AUDYT_KONTROLE")],
        packages=[DbPackage(name="PKG_AUDYT"), DbPackage(name="PKG_IMPORT_KONTROLI")],
    )
```

**c)** Update the import on line 4-6 — add `DynamicAction`, `DynamicActionStep`:
```python
from apex_export_to_md.models.apex_models import (
    ApexApp, ApexPage, Region, Process, LOV, Validation,
    DynamicAction, DynamicActionStep,
)
```

**d)** Add new test classes at the end of the file:

```python
class TestPackageLinking:
    def test_package_detected_in_process_code(self, db_schema):
        app = ApexApp(
            name="TEST", id="1", alias="T",
            pages=[
                ApexPage(id=1, name="Test",
                    processes=[
                        Process(name="Zamroz", type="PL/SQL",
                                code="PKG_AUDYT.ZAMROZ_AUDYT(:P1_ID);"),
                    ],
                ),
            ],
        )
        linker = ApexDbLinker(app, db_schema)
        links = linker.find_links()
        all_objects = set()
        for l in links:
            all_objects.update(l.db_objects)
        assert "PKG_AUDYT" in all_objects

    def test_package_not_false_positive(self, db_schema):
        """Nazwa pakietu nie powinna matchować częściowo."""
        app = ApexApp(
            name="TEST", id="1", alias="T",
            pages=[
                ApexPage(id=1, name="Test",
                    processes=[
                        Process(name="Proc", type="PL/SQL",
                                code="-- Komentarz bez referencji do pakietu"),
                    ],
                ),
            ],
        )
        linker = ApexDbLinker(app, db_schema)
        links = linker.find_links()
        assert len(links) == 0
```

- [ ] **Step 2: Write failing tests for dynamic actions scanning**

Add class `TestDynamicActionScanning` at the end of the file (imports already updated in Step 1c):

```python
class TestDynamicActionScanning:
    def test_dynamic_action_plsql_code_scanned(self, db_schema):
        app = ApexApp(
            name="TEST", id="1", alias="T",
            pages=[
                ApexPage(id=1, name="Test",
                    dynamic_actions=[
                        DynamicAction(
                            name="On Change",
                            event="Change",
                            actions=[
                                DynamicActionStep(
                                    type="Execute PL/SQL Code",
                                    code="SELECT 1 FROM B_AUDYT WHERE ID = :P1_ID",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        linker = ApexDbLinker(app, db_schema)
        links = linker.find_links()
        da_links = [l for l in links if l.source_type == "dynamic_action"]
        assert len(da_links) == 1
        assert "B_AUDYT" in da_links[0].db_objects

    def test_dynamic_action_js_not_scanned(self, db_schema):
        """JS-only dynamic actions bez SQL nie tworzą linków."""
        app = ApexApp(
            name="TEST", id="1", alias="T",
            pages=[
                ApexPage(id=1, name="Test",
                    dynamic_actions=[
                        DynamicAction(
                            name="Hide",
                            event="Click",
                            actions=[
                                DynamicActionStep(
                                    type="Execute JavaScript Code",
                                    code="$('#region').hide();",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        linker = ApexDbLinker(app, db_schema)
        links = linker.find_links()
        assert len(links) == 0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_apex_db_linker.py::TestPackageLinking tests/test_apex_db_linker.py::TestDynamicActionScanning -v`
Expected: FAIL

- [ ] **Step 4: Add packages to _db_names in linker**

In `apex_db_linker.py`, modify `__init__` (line 30-33):
```python
        self._db_names = sorted(
            [t.name for t in schema.tables]
            + [v.name for v in schema.views]
            + [p.name for p in schema.packages],
            key=lambda x: -len(x),
        )
```

- [ ] **Step 5: Add dynamic actions scanning to _scan_page**

In `apex_db_linker.py`, in `_scan_page`, after the validations block (after line 108), add:
```python
        # Dynamic actions (tylko PL/SQL code)
        for da in page.dynamic_actions:
            da_objects: list[str] = []
            for step in da.actions:
                if step.code and "SQL" in (step.type or "").upper():
                    da_objects.extend(self._find_db_objects_in_sql(step.code))
            da_objects = list(dict.fromkeys(da_objects))
            if da_objects:
                links.append(ApexDbLink(
                    page_id=page.id, page_name=page.name,
                    db_objects=da_objects,
                    source_type="dynamic_action", source_name=da.name,
                ))
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_apex_db_linker.py -v`
Expected: PASS

- [ ] **Step 7: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add apex_export_to_md/linker/apex_db_linker.py tests/test_apex_db_linker.py
git commit -m "feat(linker): linkowanie APEX→pakiety PL/SQL + skanowanie dynamic actions"
```

---

### Task 8: Integration verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all PASS, no regressions

- [ ] **Step 2: Run integration test with real DDL**

Run: `python -m pytest tests/test_integration_ddl.py -v`
Expected: PASS — error codes extracted from PKG_AUDYT, NOCACHE on sequences

- [ ] **Step 3: Final commit if any adjustments needed**
