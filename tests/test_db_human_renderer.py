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

    def test_error_codes_rendered(self, config, sample_schema):
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

    def test_mermaid_fk_relationship(self, config, sample_schema):
        r = DbHumanRenderer(config)
        result = r.render(sample_schema)
        assert "B_AUDYT" in result
        assert "B_ANKIETA" in result
