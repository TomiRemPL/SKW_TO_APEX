"""Testy kompletności czytelnego renderera DDL."""
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp
from apex_export_to_md.renderers.ddl_human_renderer import DDLHumanRenderer


def test_renderuje_wszystkie_typy_obiektow_ddl(rich_ddl_app: ApexApp):
    """Dokumentacja musi wskazywać każdy typ obiektu dostępny w modelu DDL."""
    output = DDLHumanRenderer(AppConfig()).render(rich_ddl_app)

    for expected in (
        "`PARENT`", "`CHILD`", "`CHILD_V`", "`CHILD_PKG`", "`SYNC_CHILD`",
        "`CHILD_SEQ`", "`CHILD_CODE_IDX`", "`CHILD_BI`",
    ):
        assert expected in output


def test_renderuje_atrybuty_tabel_i_ograniczenia(rich_ddl_app: ApexApp):
    """Kolumny, komentarze i wszystkie typy ograniczeń zachowują znaczenie."""
    output = DDLHumanRenderer(AppConfig()).render(rich_ddl_app)

    for expected in (
        "`ID`", "`PARENT_ID`", "`CODE`", "Kod biznesowy", "CHILD_PARENT_FK",
        "CHILD_CODE_UK (UNIQUE)", "CHILD_CODE_CHK (CHECK)", "CODE IS NOT NULL",
    ):
        assert expected in output


def test_renderuje_kod_tylko_w_trybie_full(rich_ddl_app: ApexApp):
    full = DDLHumanRenderer(AppConfig(include_code="full")).render(rich_ddl_app)
    none = DDLHumanRenderer(AppConfig(include_code="none")).render(rich_ddl_app)

    assert "SELECT ID, CODE FROM CHILD" in full
    assert "SELECT ID, CODE FROM CHILD" not in none