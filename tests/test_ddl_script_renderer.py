"""Testy DDLScriptRenderer — minimalny skrypt SQL bez klauzul storage/tablespace."""
from __future__ import annotations
import tempfile
from pathlib import Path

import pytest

from apex_export_to_md.parser.ddl_parser import parse_ddl_file
from apex_export_to_md.renderers.ddl_script_renderer import DDLScriptRenderer
from apex_export_to_md.models import ApexApp, DDLColumn
from apex_export_to_md.config import AppConfig

# Przykład zbliżony do realnego DDL pobieranego automatycznie z bazy
# (DBMS_METADATA), z niecytowanym wzorcem SCHEMAT.SEKWENCJA.NEXTVAL
# oraz pełnymi klauzulami STORAGE/TABLESPACE/LOB.
RAW_DDL = """
CREATE TABLE "DAW"."A_PYTANIE"
   (\t"ID_PYTANIE" NUMBER DEFAULT ON NULL DAW.DAW_SEQ_A_PYTANIE_PK.NEXTVAL NOT NULL ENABLE,
\t"PYTANIE_TRESC" VARCHAR2(1024 CHAR) NOT NULL ENABLE,
\t"PYTANIE_POMOC" VARCHAR2(4000),
\t"PYTANIE_OD" DATE DEFAULT '1900-01-01',
\t"PYTANIE_DODATKOWE_RZECZY" CLOB,
\t CONSTRAINT "A_PYTANIE_PK" PRIMARY KEY ("ID_PYTANIE")
  USING INDEX PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645)
  TABLESPACE "APEX_7655264491003440"  ENABLE
   ) SEGMENT CREATION IMMEDIATE
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255
 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645)
  TABLESPACE "APEX_7655264491003440"
 LOB ("PYTANIE_DODATKOWE_RZECZY") STORE AS SECUREFILE (
  TABLESPACE "APEX_7655264491003440" ENABLE STORAGE IN ROW CHUNK 8192
  NOCACHE LOGGING  NOCOMPRESS) ;

CREATE SEQUENCE "DAW"."DAW_SEQ_A_PYTANIE_PK"  MINVALUE 1 MAXVALUE 9999999999999999999999999999
 INCREMENT BY 1 START WITH 39 CACHE 20 NOORDER  NOCYCLE ;

CREATE INDEX "DAW"."A_PYTANIE_IDX1" ON "DAW"."A_PYTANIE" ("PYTANIE_TRESC")
  PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645)
  TABLESPACE "APEX_7655264491003440" ;
"""


@pytest.fixture
def ddl_app() -> ApexApp:
    with tempfile.TemporaryDirectory() as tmp:
        ddl_path = Path(tmp) / "auto_ddl_OnSiteApp.sql"
        ddl_path.write_text(RAW_DDL, encoding="utf-8")
        schema = parse_ddl_file(ddl_path)
    app = ApexApp(name="Test", id="1")
    app.ddl_schema = schema
    return app


def test_source_schema_detected_from_unquoted_nextval(ddl_app: ApexApp):
    """Bug fix: schemat DAW ma być wykryty nawet z niecytowanego DAW.SEQ.NEXTVAL."""
    assert ddl_app.ddl_schema.source_schema == "DAW"


def test_table_has_no_storage_or_tablespace_clauses(ddl_app: ApexApp):
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    for forbidden in ("STORAGE(", "TABLESPACE", "PCTFREE", "SEGMENT CREATION", "SECUREFILE"):
        assert forbidden not in output, f"'{forbidden}' nie powinno wystąpić w minimalnym DDL"


def test_table_schema_qualifier_stripped(ddl_app: ApexApp):
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    assert '"DAW".' not in output
    assert 'CREATE TABLE "A_PYTANIE"' in output


def test_enable_only_on_not_null_or_identity_columns(ddl_app: ApexApp):
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    assert '"PYTANIE_POMOC" VARCHAR2(4000),' in output
    assert '"PYTANIE_DODATKOWE_RZECZY" CLOB' in output
    assert "PYTANIE_OD\" DATE DEFAULT TO_DATE('1900-01-01', 'YYYY-MM-DD'),\n" in output
    assert '"PYTANIE_TRESC" VARCHAR2(1024 CHAR) NOT NULL ENABLE' in output


def test_primary_key_uses_plain_using_index_enable(ddl_app: ApexApp):
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    assert 'CONSTRAINT "A_PYTANIE_PK" PRIMARY KEY ("ID_PYTANIE") USING INDEX ENABLE' in output


def test_sequence_default_kept_as_nextval_without_schema(ddl_app: ApexApp):
    """Zgodnie z decyzją: brak konwersji na IDENTITY, sekwencja i jej nazwa zachowane."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    assert "DEFAULT ON NULL DAW_SEQ_A_PYTANIE_PK.NEXTVAL NOT NULL ENABLE" in output
    assert 'CREATE SEQUENCE "DAW_SEQ_A_PYTANIE_PK"' in output


def test_index_minimal_without_storage(ddl_app: ApexApp):
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)
    assert 'CREATE INDEX "A_PYTANIE_IDX1" ON "A_PYTANIE" ("PYTANIE_TRESC");' in output


def test_multiline_comments_empty_lines_and_semicolons_stripped(ddl_app: ApexApp):
    """Komentarze tabel/kolumn nie powinny zawierać pustych linii ani średników w wygenerowanym DDL."""
    from apex_export_to_md.models import DDLTable

    table = DDLTable(
        name="TEST_TABLE",
        comment="Linia 1; opis z średnikiem;\n  \n\nLinia 2 z tekstem;\n\t\nLinia 3",
        column_comments={
            "COL1": "Opis kolumny 1; z średnikiem\n\nOpis kolumny 1 c.d."
        }
    )
    ddl_app.ddl_schema.tables.append(table)

    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)

    # Sprawdzenie komentarza tabeli
    expected_table_comment = "COMMENT ON TABLE \"TEST_TABLE\" IS 'Linia 1 opis z średnikiem\nLinia 2 z tekstem\nLinia 3';"
    assert expected_table_comment in output

    # Sprawdzenie komentarza kolumny
    expected_col_comment = "COMMENT ON COLUMN \"TEST_TABLE\".\"COL1\" IS 'Opis kolumny 1 z średnikiem\nOpis kolumny 1 c.d.';"
    assert expected_col_comment in output


def test_no_consecutive_empty_lines_or_whitespace_lines(ddl_app: ApexApp):
    """Skrypt DDL nie powinien zawierać kolejnych pustych linii ani linii składających się z samych spacji."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(ddl_app)

    lines = output.split("\n")
    for i, line in enumerate(lines):
        # Brak spacji w pustych liniach
        if not line.strip():
            assert line == "", f"Linia {i+1} zawiera same białe znaki: {repr(line)}"
        # Brak dwóch kolejnych pustych linii
        if i > 0 and line == "" and lines[i-1] == "":
            pytest.fail(f"Znaleziono podwójną pustą linię w linii {i+1}")


def _render_column_default(col: DDLColumn, schema: str = "DAW") -> str:
    """Zbuduj tabelę z jedną kolumną i zwróć wyrenderowaną definicję tej kolumny."""
    from apex_export_to_md.models import DDLTable, DDLSchema
    table = DDLTable(name="TEST_DEFAULT", columns=[col])
    ddl_schema = DDLSchema(source_schema=schema)
    ddl_schema.tables.append(table)
    app = ApexApp(name="Test", id="1")
    app.ddl_schema = ddl_schema
    output = DDLScriptRenderer(AppConfig()).render(app)
    for line in output.splitlines():
        if f'"{col.name}"' in line and "CREATE TABLE" not in line:
            return line
    pytest.fail(f"Nie znaleziono definicji kolumny {col.name} w:\n{output}")


def test_date_iso_literal_wrapped_in_to_date():
    """Literał ISO daty w kolumnie DATE → TO_DATE z maską YYYY-MM-DD."""
    col = DDLColumn(name="C", data_type="DATE", default="'1900-01-01'")
    line = _render_column_default(col)
    assert line == '    "C" DATE DEFAULT TO_DATE(\'1900-01-01\', \'YYYY-MM-DD\')'


def test_timestamp_with_time_wrapped_in_to_timestamp():
    """Literał daty z czasem w kolumnie TIMESTAMP → TO_TIMESTAMP z maską z czasem."""
    col = DDLColumn(name="C", data_type="TIMESTAMP(6)", default="'2020-01-15 10:30:00'")
    line = _render_column_default(col)
    assert line == '    "C" TIMESTAMP(6) DEFAULT TO_TIMESTAMP(\'2020-01-15 10:30:00\', \'YYYY-MM-DD HH24:MI:SS\')'


def test_timestamp_with_fractional_seconds():
    """Literał z ułamkiem sekund → maska z FF."""
    col = DDLColumn(name="C", data_type="TIMESTAMP", default="'2020-01-15 10:30:00.123'")
    line = _render_column_default(col)
    assert line == '    "C" TIMESTAMP DEFAULT TO_TIMESTAMP(\'2020-01-15 10:30:00.123\', \'YYYY-MM-DD HH24:MI:SS.FF\')'


def test_date_oracle_mon_rr_wrapped_with_nls_date_language():
    """Wzorzec DD-MON-RR → TO_DATE z NLS_DATE_LANGUAGE=ENGLISH."""
    col = DDLColumn(name="C", data_type="DATE", default="'01-JAN-23'")
    line = _render_column_default(col)
    assert line == '    "C" DATE DEFAULT TO_DATE(\'01-JAN-23\', \'DD-MON-RR\', \'NLS_DATE_LANGUAGE=ENGLISH\')'


def test_date_sysdate_left_unchanged():
    """Funkcja SYSDATE nie jest czystym literałem → bez zmian."""
    col = DDLColumn(name="C", data_type="DATE", default="SYSDATE")
    line = _render_column_default(col)
    assert line == '    "C" DATE DEFAULT SYSDATE'


def test_date_nextval_left_unchanged():
    """Wywołanie seq.NEXTVAL (z prefiksem schematu) → bez konwersji, schema usunięty."""
    col = DDLColumn(name="C", data_type="DATE", default="DAW.SEQ_X.NEXTVAL")
    line = _render_column_default(col, schema="DAW")
    assert line == '    "C" DATE DEFAULT SEQ_X.NEXTVAL'


# ---------------------------------------------------------------------------
# Testy pakietów PL/SQL
# ---------------------------------------------------------------------------

PKG_DDL = """
CREATE OR REPLACE PACKAGE "DAW"."PKG_TEST" AS
    FUNCTION GET_VALUE (p_id IN NUMBER) RETURN VARCHAR2;
    PROCEDURE DO_SOMETHING (p_id IN NUMBER);
END PKG_TEST;
/
CREATE OR REPLACE PACKAGE BODY "DAW"."PKG_TEST" AS
    FUNCTION GET_VALUE (p_id IN NUMBER) RETURN VARCHAR2 IS
        v_result VARCHAR2(200);
    BEGIN
        SELECT NAME INTO v_result FROM DAW.SOME_TABLE WHERE ID = p_id;
        RETURN v_result;
    END GET_VALUE;
    PROCEDURE DO_SOMETHING (p_id IN NUMBER) AS
        v_num NUMBER;
    BEGIN
        v_num := p_id * 2;
        UPDATE DAW.SOME_TABLE SET VAL = v_num WHERE ID = p_id;
    END DO_SOMETHING;
END PKG_TEST;
/
"""

PKG_DDL_SPEC_ONLY = """
CREATE OR REPLACE PACKAGE "DAW"."PKG_SPEC_ONLY" AS
    FUNCTION GET_VAL RETURN NUMBER;
END PKG_SPEC_ONLY;
/
"""


@pytest.fixture
def pkg_app() -> ApexApp:
    with tempfile.TemporaryDirectory() as tmp:
        ddl_path = Path(tmp) / "pkg.sql"
        ddl_path.write_text(PKG_DDL, encoding="utf-8")
        schema = parse_ddl_file(ddl_path)
    app = ApexApp(name="PkgTest", id="99")
    app.ddl_schema = schema
    return app


@pytest.fixture
def pkg_spec_only_app() -> ApexApp:
    with tempfile.TemporaryDirectory() as tmp:
        ddl_path = Path(tmp) / "pkg_spec.sql"
        ddl_path.write_text(PKG_DDL_SPEC_ONLY, encoding="utf-8")
        schema = parse_ddl_file(ddl_path)
    app = ApexApp(name="PkgSpecOnly", id="98")
    app.ddl_schema = schema
    return app


def test_package_renders_separate_spec_and_body(pkg_app: ApexApp):
    """Pakiet z body → dwa osobne bloki DDL: PACKAGE spec i PACKAGE BODY."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    assert "CREATE OR REPLACE PACKAGE PKG_TEST AS" in output
    assert "CREATE OR REPLACE PACKAGE BODY PKG_TEST AS" in output


def test_package_spec_contains_only_signatures(pkg_app: ApexApp):
    """Specyfikacja pakietu nie może zawierać deklaracji zmiennych ani BEGIN."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    spec_block = output.split("CREATE OR REPLACE PACKAGE BODY")[0]
    assert "v_result" not in spec_block
    assert "v_num" not in spec_block
    assert "BEGIN" not in spec_block


def test_package_body_contains_implementation(pkg_app: ApexApp):
    """Body pakietu zawiera implementacje funkcji i procedur."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    body_block = output.split("CREATE OR REPLACE PACKAGE BODY PKG_TEST AS")[1]
    assert "v_result VARCHAR2(200)" in body_block
    assert "v_num NUMBER" in body_block


def test_package_body_not_duplicated(pkg_app: ApexApp):
    """Body pakietu nie może być zduplikowane w wyjściowym SQL."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    assert output.count("CREATE OR REPLACE PACKAGE BODY PKG_TEST AS") == 1


def test_package_schema_stripped_from_body(pkg_app: ApexApp):
    """Prefiksy schematu DAW. usunięte z kodu body."""
    pkg_app.ddl_schema.source_schema = "DAW"  # wymuszamy schemat — parser nie wykryje go bez tabel/sekwencji
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    assert '"DAW".' not in output
    assert 'DAW.SOME_TABLE' not in output


def test_package_spec_only_no_body_block(pkg_spec_only_app: ApexApp):
    """Pakiet bez body → tylko blok PACKAGE spec, bez PACKAGE BODY."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_spec_only_app)
    assert "CREATE OR REPLACE PACKAGE PKG_SPEC_ONLY AS" in output
    assert "CREATE OR REPLACE PACKAGE BODY" not in output


def test_package_body_marker_not_in_sql_output(pkg_app: ApexApp):
    """Wewnętrzny marker -- PACKAGE BODY -- nie powinien trafić do finalnego SQL."""
    renderer = DDLScriptRenderer(AppConfig())
    output = renderer.render(pkg_app)
    assert "-- PACKAGE BODY --" not in output



def test_varchar_literal_left_unchanged():
    """Literał tekstowy w kolumnie nie-daty → bez konwersji."""
    col = DDLColumn(name="C", data_type="VARCHAR2(100)", default="'abc'")
    line = _render_column_default(col)
    assert line == '    "C" VARCHAR2(100) DEFAULT \'abc\''


def test_date_unrecognized_format_left_unchanged():
    """Nierozpoznany format daty → DEFAULT bez zmian (z WARNING w logach)."""
    col = DDLColumn(name="C", data_type="DATE", default="'01/02/03'")
    line = _render_column_default(col)
    assert line == '    "C" DATE DEFAULT \'01/02/03\''


