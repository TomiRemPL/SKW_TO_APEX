"""Testy filtra stron APEX."""
from apex_export_to_md.filters.page_filter import PageFilter
from apex_export_to_md.models import ApexPage
from apex_export_to_md.config import AppConfig


def _make_page(id: int, name: str, page_group: str | None = None,
               security: dict | None = None) -> ApexPage:
    return ApexPage(id=id, name=name, page_group=page_group,
                    security=security or {})


def test_auto_filtruje_admin():
    """Strony z grupy Administration są pomijane."""
    f = PageFilter(AppConfig(page_filter="auto"))
    pages = [
        _make_page(4, "DAW_LISTA_AUDYTOW"),
        _make_page(10000, "Administration", page_group="Administration"),
    ]
    result = f.filter_pages(pages)
    assert len(result) == 1
    assert result[0].name == "DAW_LISTA_AUDYTOW"


def test_auto_filtruje_user_settings():
    """Strony z grupy User Settings są pomijane."""
    f = PageFilter(AppConfig(page_filter="auto"))
    pages = [_make_page(20000, "Settings", page_group="User Settings")]
    assert len(f.filter_pages(pages)) == 0


def test_auto_filtruje_admin_rights():
    """Strony z authorization-scheme Administration Rights są pomijane."""
    f = PageFilter(AppConfig(page_filter="auto"))
    pages = [_make_page(
        10010, "Config",
        security={"authorization-scheme": "Administration Rights # 123"},
    )]
    assert len(f.filter_pages(pages)) == 0


def test_auto_filtruje_system_pages():
    """Global Page i Login Page są pomijane."""
    f = PageFilter(AppConfig(page_filter="auto"))
    pages = [
        _make_page(0, "Global Page"),
        _make_page(9999, "Login Page"),
        _make_page(4, "DAW_LISTA"),
    ]
    result = f.filter_pages(pages)
    assert len(result) == 1


def test_filtr_all():
    """Tryb 'all' — brak filtrowania."""
    f = PageFilter(AppConfig(page_filter="all"))
    pages = [
        _make_page(0, "Global Page"),
        _make_page(4, "DAW_LISTA_AUDYTOW"),
        _make_page(10000, "Administration", page_group="Administration"),
    ]
    assert len(f.filter_pages(pages)) == 3


def test_filtr_prefix():
    """Tryb 'prefix:DAW_' — filtr po prefiksie nazwy."""
    f = PageFilter(AppConfig(page_filter="prefix:DAW_"))
    pages = [
        _make_page(1, "Home"),
        _make_page(4, "DAW_LISTA_AUDYTOW"),
        _make_page(5, "DAW_IMPORT"),
    ]
    result = f.filter_pages(pages)
    assert len(result) == 2


def test_filtr_ids():
    """Tryb 'ids:4,5' — filtr po ID."""
    f = PageFilter(AppConfig(page_filter="ids:4,5"))
    pages = [
        _make_page(1, "Home"),
        _make_page(4, "DAW_LISTA"),
        _make_page(5, "DAW_IMPORT"),
    ]
    result = f.filter_pages(pages)
    assert len(result) == 2


def test_extra_pages():
    """Extra pages dodają strony pominięte przez filtr auto."""
    f = PageFilter(AppConfig(page_filter="auto", extra_pages=[1]))
    pages = [
        _make_page(0, "Global Page"),
        _make_page(1, "Home"),
        _make_page(4, "DAW_LISTA"),
    ]
    result = f.filter_pages(pages)
    assert len(result) == 2
    ids = [p.id for p in result]
    assert 1 in ids
    assert 4 in ids
