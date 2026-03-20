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
