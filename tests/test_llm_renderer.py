"""Testy LLM renderera (format skondensowany)."""
from apex_export_to_md.renderers.llm_renderer import LLMRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, Button,
    Authorization, AppItem, BuildOption, AclRole, DynamicAction,
    DynamicActionStep, AppMetadata,
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


def test_render_build_option():
    app = _make_app()
    app.pages[0].dynamic_actions[0].build_option = "Commented Out"
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(app)
    assert "DA:Zmiana|event:Change|sel:Item|trigger:P4_STATUS|build_opt:Commented Out" in output


def test_render_zawiera_konfiguracje_techniczna():
    """Zapisuje konfigurację eksportu SQL w skondensowanym formacie."""
    app = _make_app()
    app.metadata = AppMetadata(
        compatibility_mode="21.2",
        page_protection_enabled=True,
        bookmark_checksum_function="SH512",
        security_scheme="MUST_NOT_BE_PUBLIC_USER",
        files_version=13,
    )
    output = LLMRenderer(AppConfig()).render(app)
    assert "META:|COMPAT=21.2|PAGE_PROTECTION=Y|BOOKMARK_CHECKSUM=SH512" in output
    assert "SECURITY=MUST_NOT_BE_PUBLIC_USER" in output
    assert "FILES_VER=13" in output


def test_render_dane_semantyczne():
    """Format LLM zapisuje zwięzłe informacje o źródle i procesie DML."""
    app = _make_app()
    region = app.pages[0].regions[0]
    region.source_owner = "DAW"
    region.source_where = "STATUS = 'Otwarty'"
    app.pages[0].processes[0].target_type = "REGION_SOURCE"
    app.pages[0].processes[0].prevent_lost_updates = True

    output = LLMRenderer(AppConfig()).render(app)

    assert "src:DAW.B_AUDYT" in output
    assert "where:STATUS = 'Otwarty'" in output
    assert "target:REGION_SOURCE" in output
    assert "prevent_lost_update:true" in output
