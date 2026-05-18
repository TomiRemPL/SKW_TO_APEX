"""Testy modeli danych APEX."""
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, DynamicAction,
    DynamicActionStep, Button, Branch,
)


def test_tworzenie_strony_minimalne():
    """Strona z wymaganymi polami i domyślnymi wartościami."""
    page = ApexPage(id=4, name="DAW_LISTA_AUDYTOW")
    assert page.id == 4
    assert page.regions == []
    assert page.page_mode == "Normal"
    assert page.css_inline is None


def test_tworzenie_regionu_z_kolumnami():
    """Region z kolumnami i informacją o edytowalności."""
    col = Column(name="ID_PK", type="Hidden", primary_key=True)
    region = Region(
        name="ListaAudytow",
        type="Interactive Grid",
        source_table="B_AUDYT",
        editable=True,
        allowed_operations=["Add Row", "Update Row"],
        columns=[col],
    )
    assert region.columns[0].primary_key is True
    assert region.editable is True
    assert len(region.allowed_operations) == 2


def test_lov_trzy_typy():
    """LOV obsługuje trzy typy źródeł."""
    lov_table = LOV(name="AUDYT", source_type="Table / View", source_table="B_AUDYT")
    lov_sql = LOV(name="KONTROLE", source_type="SQL Query", sql_query="SELECT ...")
    lov_static = LOV(
        name="TAK_NIE",
        source_type="Static Values",
        entries=[{"display": "Tak", "return": "1"}],
    )
    assert lov_table.source_table == "B_AUDYT"
    assert lov_sql.sql_query == "SELECT ..."
    assert lov_static.entries[0]["display"] == "Tak"


def test_proces_z_przyciskiem():
    """Proces powiązany z przyciskiem."""
    proc = Process(
        name="Zapisz",
        type="Execute Code",
        language="PL/SQL",
        point="After Submit",
        code="BEGIN PKG.SAVE; END;",
        when_button_pressed="SAVE",
    )
    assert proc.when_button_pressed == "SAVE"
    assert proc.language == "PL/SQL"


def test_dynamic_action_z_krokami():
    """DA z listą kroków."""
    step = DynamicActionStep(type="Execute PL/SQL Code", code="BEGIN NULL; END;")
    da = DynamicAction(
        name="Zmiana_statusu",
        event="Change",
        selection_type="Item",
        trigger_selector="P4_STATUS",
        actions=[step],
    )
    assert len(da.actions) == 1
    assert da.actions[0].type == "Execute PL/SQL Code"


def test_apex_app_agregat():
    """ApexApp łączy wszystkie komponenty."""
    app = ApexApp(
        name="SKW_2_APEX",
        id="160",
        alias="START338",
        pages=[ApexPage(id=1, name="Home")],
        lovs=[LOV(name="LOV1", source_type="Table / View")],
    )
    assert len(app.pages) == 1
    assert len(app.lovs) == 1
