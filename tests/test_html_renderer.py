"""Testy HTML renderera."""
from apex_export_to_md.renderers.html_renderer import HTMLRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp, ApexPage, AppMetadata, Button, Process, Region


def test_html_renderer_serialize_page_build_option():
    """HTMLRenderer poprawnie serializuje build_option w JSON."""
    proc = Process(name="Proc1", type="Execute Code", build_option="Commented Out")
    page = ApexPage(id=1, name="P1", processes=[proc])
    app = ApexApp(name="App", id="100", pages=[page])

    renderer = HTMLRenderer(AppConfig())
    serialized = renderer._serialize_page(page)
    assert serialized["processes"][0]["build_option"] == "Commented Out"

    output = renderer.render(app)
    assert "<!DOCTYPE html>" in output
    assert "Commented Out" in output


def test_html_renderer_zawiera_konfiguracje_techniczna():
    """HTML pokazuje metadane techniczne z eksportu SQL aplikacji."""
    app = ApexApp(
        name="App",
        id="100",
        metadata=AppMetadata(
            compatibility_mode="21.2",
            page_protection_enabled=True,
            bookmark_checksum_function="SH512",
            security_scheme="MUST_NOT_BE_PUBLIC_USER",
            file_storage="DB",
            files_version=13,
        ),
    )

    output = HTMLRenderer(AppConfig()).render(app)

    assert "Konfiguracja techniczna" in output
    assert "Tryb zgodności APEX" in output
    assert "21.2" in output
    assert "Ochrona stron" in output
    assert "SH512" in output
    assert "MUST_NOT_BE_PUBLIC_USER" in output
    assert "Magazyn plików statycznych" in output


def test_html_renderer_javascript_obsluguje_zakladki_bez_bledu_skladni():
    """Skrypt zakładek nie zawiera osieroconego fragmentu JavaScript."""
    script = HTMLRenderer(AppConfig())._app_js()

    assert "function switchTab(name)" in script
    assert "return html;\n}\n\n// === SHARED COMPONENTS ===" in script


def test_html_renderer_serializuje_dane_semantyczne():
    """HTML przekazuje do widoku dane funkcjonalne regionu i procesu."""
    page = ApexPage(
        id=1,
        name="P1",
        regions=[Region(name="R1", type="Form", source_table="B_AUDYT", source_owner="DAW",
                        source_where="STATUS = 'Otwarty'", lost_update_type="Row Values")],
        buttons=[Button(name="SAVE", confirmation_message="Zapisać?")],
        processes=[Process(name="Zapisz", type="DML", target_type="REGION_SOURCE",
                           prevent_lost_updates=True, success_message="Zapisano")],
    )
    serialized = HTMLRenderer(AppConfig())._serialize_page(page)

    assert serialized["regions"][0]["source_owner"] == "DAW"
    assert serialized["regions"][0]["lost_update_type"] == "Row Values"
    assert serialized["buttons"][0]["confirmation_message"] == "Zapisać?"
    assert serialized["processes"][0]["prevent_lost_updates"] is True


def test_html_renderer_shared_components_serialization():
    """HTMLRenderer poprawnie serializuje Shared Components w JSON."""
    from apex_export_to_md.models import LOV, Authorization, NavList, AppItem
    app = ApexApp(
        name="TestApp",
        id="101",
        lovs=[LOV(name="LOV1", source_type="Static Values", entries=[{"display": "A", "return": "1"}])],
        authorizations=[Authorization(name="AUTH1", type="PL/SQL Expression", code="1=1")],
        nav_lists=[NavList(name="NL1", entries=[{"label": "Strona główna", "target_page": "1"}])],
        app_items=[AppItem(name="ITEM1", scope="Application")]
    )
    renderer = HTMLRenderer(AppConfig())
    serialized_json = renderer._build_data_json(app)
    
    assert "LOV1" in serialized_json
    assert "AUTH1" in serialized_json
    assert "NL1" in serialized_json
    assert "ITEM1" in serialized_json
    
    output = renderer.render(app)
    assert "Shared Components" in output
    assert "switchTab('shared')" in output
    assert "Static Values" in output
    assert "Wartości statyczne" in output


def test_html_renderer_search_elements_and_js():
    """Test weryfikujący obecność pola wyszukiwania, panelu wyników i logiki JS dla wyszukiwarki."""
    app = ApexApp(name="TestApp", id="101")
    renderer = HTMLRenderer(AppConfig())
    output = renderer.render(app)

    # HTML elements
    assert '<div class="search-box">' in output
    assert 'id="search"' in output
    assert 'id="search-results"' in output
    assert 'oninput="handleSearch(this.value)"' in output

    # JS search functions
    assert 'function handleSearch(q)' in output
    assert 'function buildSearchIndex()' in output
    assert 'function navigateToSearchResult(el)' in output
    assert 'function hideSearchResults()' in output
    assert 'function highlightSubComponent(type, name)' in output
    assert 'search-highlight' in output


