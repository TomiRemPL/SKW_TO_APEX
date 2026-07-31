"""Testy kontraktu kluczowych informacji renderera DDL dla LLM."""
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp
from apex_export_to_md.renderers.ddl_llm_renderer import DDLLLMRenderer


def test_renderuje_kluczowe_fakty_o_obiektach_ddl(rich_ddl_app: ApexApp):
    """LLM otrzymuje identyfikatory wszystkich typów obiektów schematu."""
    output = DDLLLMRenderer(AppConfig()).render(rich_ddl_app)

    for expected in (
        "===TBL:PARENT", "===TBL:CHILD", "===VIEW:CHILD_V", "===PKG:CHILD_PKG",
        "===DDL_PROC:SYNC_CHILD", "===SEQ:CHILD_SEQ|start:10|incr:5",
        "IDX:CHILD_CODE_IDX|tbl:CHILD|cols:CODE|unique:true", "===TRG:CHILD_BI|tbl:CHILD",
    ):
        assert expected in output


def test_renderuje_atrybuty_kolumn_i_wszystkie_ograniczenia(rich_ddl_app: ApexApp):
    """Format zwięzły zachowuje fakty niezbędne do analizy relacji i integralności."""
    output = DDLLLMRenderer(AppConfig()).render(rich_ddl_app)

    for expected in (
        "TBLCOL:ID|NUMBER|nn:true|pk:true|identity:true",
        "TBLCOL:CODE|VARCHAR2(20)|def:'NEW'",
        "FK:PARENT_ID->PARENT.ID", "UNQ:CHILD_CODE_UK|CODE",
        "CHK:CHILD_CODE_CHK|CODE IS NOT NULL", "TBLCOL_COMMENT:CODE|Kod biznesowy",
    ):
        assert expected in output


def test_renderuje_kod_tylko_w_trybie_full(rich_ddl_app: ApexApp):
    full = DDLLLMRenderer(AppConfig(include_code="full")).render(rich_ddl_app)
    none = DDLLLMRenderer(AppConfig(include_code="none")).render(rich_ddl_app)

    assert "SELECT ID, CODE FROM CHILD" in full
    assert "SELECT ID, CODE FROM CHILD" not in none