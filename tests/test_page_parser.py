"""Testy parsera stron APEX."""
import pytest
from apex_export_to_md.parser.page_parser import parse_page, parse_all_pages
from apex_export_to_md.models import ApexPage


def test_parse_page_podstawowe_pola(sample_page_yaml):
    """Parser wyciąga podstawowe pola strony."""
    page = parse_page(sample_page_yaml)
    assert isinstance(page, ApexPage)
    assert page.id == 4
    assert page.name == "DAW_LISTA_AUDYTOW"
    assert page.alias == "DAW-LISTA-AUDYTOW"
    assert page.page_mode == "Normal"


def test_parse_page_css_inline(sample_page_yaml):
    """Parser wyciąga inline CSS."""
    page = parse_page(sample_page_yaml)
    assert page.css_inline == ".highlight { color: red; }"


def test_parse_page_regiony(sample_page_yaml):
    """Parser wyciąga regiony z kolumnami."""
    page = parse_page(sample_page_yaml)
    assert len(page.regions) == 1
    region = page.regions[0]
    assert region.name == "ListaAudytow"
    assert region.title == "Lista audytów"
    assert region.type == "Interactive Grid"
    assert region.source_table == "B_AUDYT"
    assert region.editable is True
    assert "Add Row" in region.allowed_operations


def test_parse_page_kolumny(sample_page_yaml):
    """Parser wyciąga kolumny z regionu."""
    page = parse_page(sample_page_yaml)
    cols = page.regions[0].columns
    assert len(cols) == 2
    assert cols[0].name == "ID_PK_B_AUDYT"
    assert cols[0].primary_key is True
    assert cols[1].heading == "Numer Audytu"
    assert cols[1].link_target is not None


def test_parse_page_items(sample_page_yaml):
    """Parser wyciąga elementy formularza."""
    page = parse_page(sample_page_yaml)
    assert len(page.items) == 1
    item = page.items[0]
    assert item.name == "P4_FILTR_STATUS"
    assert item.type == "Select List"
    assert item.label == "Status"
    assert item.lov == "STATUS_AUDYTU"


def test_parse_page_buttons(sample_page_yaml):
    """Parser wyciąga przyciski."""
    page = parse_page(sample_page_yaml)
    assert len(page.buttons) == 1
    btn = page.buttons[0]
    assert btn.name == "UTWORZ_AUDYT"
    assert btn.is_hot is True
    assert btn.action == "Submit Page"


def test_parse_page_processes(sample_page_yaml):
    """Parser wyciąga procesy z kodem PL/SQL."""
    page = parse_page(sample_page_yaml)
    assert len(page.processes) == 1
    proc = page.processes[0]
    assert proc.name == "Zapisz_Dane"
    assert proc.language == "PL/SQL"
    assert "PKG_AUDYT.ZAPISZ" in proc.code
    assert proc.when_button_pressed == "SAVE"


def test_parse_page_dynamic_actions(sample_page_yaml):
    """Parser wyciąga akcje dynamiczne z krokami."""
    page = parse_page(sample_page_yaml)
    assert len(page.dynamic_actions) == 1
    da = page.dynamic_actions[0]
    assert da.name == "Zmiana_statusu"
    assert da.event == "Change"
    assert da.selection_type == "Item"
    assert da.trigger_selector == "P4_STATUS"
    assert len(da.actions) == 1
    assert da.actions[0].type == "Execute PL/SQL Code"


def test_parse_page_branches(sample_page_yaml):
    """Parser wyciąga rozgałęzienia."""
    page = parse_page(sample_page_yaml)
    assert len(page.branches) == 1
    branch = page.branches[0]
    assert branch.name == "Go To Page 6"
    assert branch.type == "Page or URL (Redirect)"


def test_parse_page_validations(sample_page_yaml):
    """Parser wyciąga walidacje."""
    page = parse_page(sample_page_yaml)
    assert len(page.validations) == 1
    val = page.validations[0]
    assert val.name == "Sprawdz_Numer"
    assert val.type == "PL/SQL Function Body"
    assert "P4_NUMER" in val.code


def test_parse_page_admin(sample_admin_page_yaml):
    """Parser poprawnie parsuje stronę admin (page_group)."""
    page = parse_page(sample_admin_page_yaml)
    assert page.page_group == "Administration"
    assert page.id == 10000
