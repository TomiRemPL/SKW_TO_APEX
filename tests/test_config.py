"""Testy modułu konfiguracji."""
from apex_export_to_md.config import AppConfig, STANDARD_PAGE_GROUPS, SYSTEM_PAGE_NAMES


def test_domyslna_konfiguracja():
    """Sprawdza, że domyślne wartości konfiguracji są poprawne."""
    cfg = AppConfig()
    assert cfg.input_dir == "_data"
    assert cfg.output_dir == "_out"
    assert cfg.output_format == "both"
    assert cfg.include_code == "full"
    assert cfg.page_filter == "auto"
    assert cfg.include_shared_components is True
    assert cfg.verbose is False
    assert cfg.extra_pages == []
    assert cfg.ddl_file == ""


def test_nadpisanie_konfiguracji():
    """Sprawdza, że wartości można nadpisać."""
    cfg = AppConfig(output_format="llm", verbose=True, extra_pages=[1, 9999])
    assert cfg.output_format == "llm"
    assert cfg.verbose is True
    assert cfg.extra_pages == [1, 9999]


def test_stale_heurystyk():
    """Sprawdza, że stałe heurystyk są zdefiniowane."""
    assert "Administration" in STANDARD_PAGE_GROUPS
    assert "Global Page" in SYSTEM_PAGE_NAMES
