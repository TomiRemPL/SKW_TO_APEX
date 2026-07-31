"""Testy DDLScriptRenderer — minimalny skrypt SQL bez klauzul storage/tablespace."""
from __future__ import annotations
import tempfile
from pathlib import Path

import pytest

from apex_export_to_md.parser.ddl_parser import parse_ddl_file
from apex_export_to_md.renderers.ddl_script_renderer import DDLScriptRenderer
from apex_export_to_md.models import ApexApp
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
    assert "PYTANIE_OD\" DATE DEFAULT '1900-01-01',\n" in output
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

