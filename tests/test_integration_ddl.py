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
