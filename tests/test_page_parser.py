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


def test_parse_page_nowe_pola_rozszerzone():
    """Parser wyciąga nowe pola stron, regionów, itemów, procesów, komputacji."""
    yaml_data = {
        "id": 31,
        "identification": {"name": "TestPage"},
        "appearance": {
            "page-mode": "Modal Dialog",
            "page-template": "Theme Default # 1",
            "template-options": ["#DEFAULT#", "t-Dialog--noUI"],
        },
        "help": {"help-text": "Opis pomocy strony"},
        "dialog": {"chained": False, "resizable": True},
        "server-cache": {"caching": "Disabled"},
        "computations": [
            {
                "identification": {"item-name": "P31_BATCH"},
                "execution": {"point": "Before Header"},
                "computation": {
                    "type": "Expression",
                    "language": "PL/SQL",
                    "pl/sql-expression": "SYSDATE",
                },
            }
        ],
        "regions": [
            {
                "identification": {"name": "Reg1", "type": "Interactive Grid"},
                "source": {"location": "Local Database", "table-name": "T1"},
                "layout": {"slot": "BODY", "sequence": 10},
                "appearance": {"template": "Standard", "template-options": ["#DEFAULT#"]},
                "server-side-condition": {"type": "Item is NOT NULL", "value": "P31_X"},
                "attributes": {"pagination": {"type": "Scroll"}},
                "columns": [
                    {
                        "identification": {"column-name": "COL1", "type": "Text"},
                        "layout": {"sequence": 10, "column-alignment": "start"},
                        "heading": {"heading": "Nagłówek", "alignment": "center"},
                        "enable-users-to": {"sort": True},
                    }
                ],
            }
        ],
        "page-items": [
            {
                "identification": {"name": "P31_ITEM1", "type": "Text"},
                "session-state": {"data-type": "VARCHAR2", "storage": "Per Session"},
                "security": {
                    "session-state-protection": "Unrestricted",
                    "store-value-encrypted-in-session-state": True,
                },
                "layout": {"region": "Reg1", "sequence": 10},
            }
        ],
        "processes": [
            {
                "identification": {"name": "Proc1", "type": "Execute Code"},
                "source": {"language": "PL/SQL", "pl/sql-code": "NULL;"},
                "execution": {"point": "After Submit"},
                "error": {
                    "display-location": "Inline in Notification",
                    "message": "Blad",
                },
            }
        ],
    }
    page = parse_page(yaml_data)

    # Strona
    assert page.page_mode == "Modal Dialog"
    assert page.page_template == "Theme Default"
    assert "t-Dialog--noUI" in page.template_options
    assert page.help_text == "Opis pomocy strony"
    assert page.dialog == {"chained": False, "resizable": True}
    assert page.server_cache == "Disabled"

    # Komputacje
    assert len(page.computations) == 1
    assert page.computations[0].item_name == "P31_BATCH"
    assert page.computations[0].code == "SYSDATE"

    # Region
    r = page.regions[0]
    assert r.template == "Standard"
    assert r.slot == "BODY"
    assert r.sequence == 10
    assert r.server_side_condition == "type=Item is NOT NULL, value=P31_X"
    assert r.pagination == "type=Scroll"

    # Kolumna
    c = r.columns[0]
    assert c.sortable is True
    assert c.column_alignment == "start"
    assert c.heading_alignment == "center"

    # Item
    it = page.items[0]
    assert it.data_type == "VARCHAR2"
    assert it.storage == "Per Session"
    assert it.session_state_protection == "Unrestricted"
    assert it.store_encrypted is True
    assert it.region == "Reg1"

    # Proces
    pr = page.processes[0]
    assert pr.error_display_location == "Inline in Notification"


def test_parse_page_build_option():
    """Parser wyciąga configuration.build-option ze wszystkich komponentów."""
    yaml_data = {
        "identification": {"id": 43, "name": "P43"},
        "dynamic-actions": [
            {
                "identification": {"name": "DA_COMMENTED"},
                "when": {"event": "Page Load"},
                "configuration": {"build-option": "Commented Out # 12345"},
            }
        ],
        "regions": [
            {
                "identification": {"name": "RGN_DISABLED"},
                "configuration": {"build-option": "Exclude"},
                "columns": [
                    {
                        "identification": {"column-name": "COL_COMMENTED"},
                        "configuration": {"build-option": "Commented Out"},
                    }
                ],
            }
        ],
        "page-items": [
            {
                "identification": {"name": "P43_ITEM_COMMENTED"},
                "configuration": {"build-option": "Commented Out"},
            }
        ],
    }
    page = parse_page(yaml_data)
    assert page.dynamic_actions[0].build_option == "Commented Out"
    assert page.regions[0].build_option == "Exclude"
    assert page.regions[0].columns[0].build_option == "Commented Out"
    assert page.items[0].build_option == "Commented Out"
