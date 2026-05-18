"""Testy LLM renderera (format skondensowany)."""
from apex_export_to_md.renderers.llm_renderer import LLMRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, Button,
    Authorization, AppItem, BuildOption, AclRole, DynamicAction,
    DynamicActionStep,
)


def _make_app() -> ApexApp:
    col = Column(name="ID_PK", type="Hidden", primary_key=True)
    col2 = Column(name="NUMER", type="Link", heading="Numer", link_target="6")
    region = Region(
        name="Lista", title="Audyty", type="Interactive Grid",
        source_table="B_AUDYT", editable=True,
        allowed_operations=["Add Row"], columns=[col, col2],
    )
    proc = Process(name="Zapisz", type="Execute Code", language="PL/SQL",
                   point="After Submit", code="BEGIN SAVE; END;",
                   when_button_pressed="SAVE")
    da = DynamicAction(
        name="Zmiana", event="Change", selection_type="Item",
        trigger_selector="P4_STATUS",
        actions=[DynamicActionStep(type="Execute PL/SQL Code", code="NULL;")],
    )
    page = ApexPage(
        id=4, name="DAW_LISTA", regions=[region],
        processes=[proc], dynamic_actions=[da],
        buttons=[Button(name="SAVE", label="Zapisz", action="Submit Page", is_hot=True)],
    )
    return ApexApp(
        name="TEST", id="100", alias="T",
        pages=[page],
        lovs=[LOV(name="L1", source_type="Table / View", source_table="T1",
                  return_column="ID", display_column="NAME")],
        authorizations=[Authorization(name="Admin", type="Is In Role",
                                       role_or_group="Adm")],
    )


def test_render_format_liniowy():
    """Sprawdza, że wyjście używa formatu liniowego z prefiksami."""
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert output.startswith("APP:100|T|TEST")
    assert "===PAGE:4|DAW_LISTA" in output


def test_render_region_kolumny():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "RGN:Lista|" in output
    assert "COL:ID_PK|Hidden|pk:true" in output
    assert "COL:NUMER|Link|heading:Numer|link:page6" in output


def test_render_process_z_kodem():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "PROC:Zapisz|" in output
    assert "BEGIN SAVE; END;" in output


def test_render_da():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "DA:Zmiana|event:Change" in output
    assert "DA_STEP:Execute PL/SQL Code" in output


def test_render_lov():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "===LOV:L1|type:Table|" in output


def test_render_bez_kodu():
    renderer = LLMRenderer(AppConfig(include_code="none"))
    output = renderer.render(_make_app())
    assert "BEGIN SAVE; END;" not in output
