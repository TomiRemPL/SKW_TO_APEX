"""Testy human renderera (Markdown)."""
from apex_export_to_md.renderers.human_renderer import HumanRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, Button,
    Authorization, AppItem, BuildOption, AclRole,
)


def _make_app_with_page() -> ApexApp:
    """Utwórz minimalną aplikację z jedną stroną do testów."""
    col = Column(name="ID_PK", type="Hidden", primary_key=True,
                 source_column="ID_PK", data_type="NUMBER")
    col2 = Column(name="NUMER", type="Link", heading="Numer",
                  source_column="NUMER", link_target="6")
    region = Region(
        name="Lista", title="Lista audytów", type="Interactive Grid",
        source_table="B_AUDYT", editable=True,
        allowed_operations=["Add Row", "Update Row"],
        columns=[col, col2],
    )
    proc = Process(name="Zapisz", type="Execute Code", language="PL/SQL",
                   point="After Submit", code="BEGIN SAVE; END;",
                   when_button_pressed="SAVE")
    btn = Button(name="SAVE", label="Zapisz", action="Submit Page", is_hot=True)
    page = ApexPage(
        id=4, name="DAW_LISTA", title="Lista",
        regions=[region], processes=[proc], buttons=[btn],
        css_inline=".row { color: red; }",
    )
    return ApexApp(
        name="TEST_APP", id="100", alias="TEST",
        pages=[page],
        lovs=[LOV(name="LOV1", source_type="Table / View",
                  source_table="T1", return_column="ID", display_column="NAME")],
        authorizations=[Authorization(name="Admin", type="Is In Role",
                                       role_or_group="Administrator")],
        app_items=[AppItem(name="G_USER", scope="Global")],
        build_options=[BuildOption(name="Feature: X", status="Include")],
        acl_roles=[AclRole(name="Admin", static_id="ADMIN")],
    )


def test_render_zawiera_naglowek():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "# Aplikacja TEST_APP" in output
    assert "ID: 100" in output


def test_render_zawiera_strone():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "### Strona 4: DAW_LISTA" in output


def test_render_zawiera_region_z_kolumnami():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "Interactive Grid" in output
    assert "B_AUDYT" in output
    assert "ID_PK" in output
    assert "NUMER" in output


def test_render_zawiera_procesy():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "BEGIN SAVE; END;" in output
    assert "Zapisz" in output


def test_render_zawiera_css():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert ".row { color: red; }" in output


def test_render_zawiera_shared_components():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "LOV1" in output
    assert "Table / View" in output
    assert "Admin" in output


def test_render_bez_kodu():
    renderer = HumanRenderer(AppConfig(include_code="none"))
    output = renderer.render(_make_app_with_page())
    assert "BEGIN SAVE; END;" not in output


def test_render_bez_shared():
    renderer = HumanRenderer(AppConfig(include_shared_components=False))
    output = renderer.render(_make_app_with_page())
    assert "LOV1" not in output
