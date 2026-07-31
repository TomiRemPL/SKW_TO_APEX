"""Parser pliku eksportu SQL aplikacji APEX (f*.sql).

Wyciąga metadane aplikacji z nagłówka pliku SQL eksportu:
- ID, nazwa, alias, wersja
- Statystyki (liczba stron, regionów, przycisków, itp.)
- Ustawienia (PWA, język, owner)
- Zmienne substytucyjne (APP_NAME, APP_COPYRIGHT, itp.)
"""
from __future__ import annotations
import re
import logging
from pathlib import Path

from apex_export_to_md.models import AppMetadata

logger = logging.getLogger(__name__)


def parse_app_sql_file(file_path: Path) -> AppMetadata | None:
    """Parsuj plik f*.sql i zwróć metadane aplikacji.

    Args:
        file_path: Ścieżka do pliku SQL eksportu APEX (np. f338.sql)

    Returns:
        AppMetadata z wyciągniętymi danymi lub None jeśli plik niepoprawny
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Nie można odczytać pliku SQL: %s — %s", file_path, e)
        return None

    meta = AppMetadata()

    # --- Nagłówek eksportu (komentarze) ---
    _parse_export_header(content, meta)

    # --- Blok import_begin (wersja APEX, owner) ---
    _parse_import_begin(content, meta)

    # --- Blok create_flow (główne parametry aplikacji) ---
    _parse_create_flow(content, meta)

    logger.info(
        "Sparsowano metadane SQL: %s (ID=%s, APEX %s, %d stron)",
        meta.app_name, meta.app_id, meta.apex_version, meta.pages_count,
    )
    return meta


def _parse_export_header(content: str, meta: AppMetadata) -> None:
    """Wyciągnij dane z komentarzy nagłówka eksportu."""
    # Application:     160
    m = re.search(r"--\s+Application:\s+(\d+)", content)
    if m:
        meta.app_id = m.group(1)

    # Name:            SKW_2_APEX
    m = re.search(r"--\s+Name:\s+(\S+)", content)
    if m:
        meta.app_name = m.group(1)

    # Exported By:     TREMBIASZ
    m = re.search(r"--\s+Exported By:\s+(\S+)", content)
    if m:
        meta.exported_by = m.group(1)

    # Version:         24.2.10
    m = re.search(r"--\s+Version:\s+([\d.]+)", content)
    if m:
        meta.apex_version = m.group(1)

    # Statystyki z nagłówka
    stats_patterns = [
        (r"--\s+Pages:\s+(\d+)", "pages_count"),
        (r"--\s+Items:\s+(\d+)", "items_count"),
        (r"--\s+Regions:\s+(\d+)", "regions_count"),
        (r"--\s+Buttons:\s+(\d+)", "buttons_count"),
        (r"--\s+Processes:\s+(\d+)", "processes_count"),
        (r"--\s+Dynamic Actions:\s+(\d+)", "dynamic_actions_count"),
        (r"--\s+Validations:\s+(\d+)", "validations_count"),
        (r"--\s+LOVs:\s+(\d+)", "lovs_count"),
        (r"--\s+Authentication:\s+(\d+)", "auth_schemes_count"),
        (r"--\s+Build Options:\s+(\d+)", "build_options_count"),
        (r"--\s+Lists:\s+(\d+)", "lists_count"),
    ]
    for pattern, attr in stats_patterns:
        m = re.search(pattern, content)
        if m:
            setattr(meta, attr, int(m.group(1)))


def _parse_import_begin(content: str, meta: AppMetadata) -> None:
    """Wyciągnij dane z bloku wwv_flow_imp.import_begin."""
    # p_release=>'24.2.10'
    m = re.search(r"p_release\s*=>\s*'([^']+)'", content)
    if m:
        meta.apex_version = m.group(1)

    # p_default_owner=>'DAW'
    m = re.search(r"p_default_owner\s*=>\s*'([^']+)'", content)
    if m:
        meta.owner = m.group(1)


def _parse_create_flow(content: str, meta: AppMetadata) -> None:
    """Wyciągnij dane z bloku create_flow (główna definicja aplikacji)."""
    # Szukaj bloku create_flow
    flow_match = re.search(
        r"create_flow\((.+?)\);", content, re.DOTALL
    )
    if not flow_match:
        return

    block = flow_match.group(1)

    # p_name => 'SKW_2_APEX'
    m = re.search(r"p_name\s*=>\s*(?:nvl\([^,]+,\s*)?'([^']+)'", block)
    if m:
        meta.app_name = m.group(1)

    # p_alias => 'START160'
    m = re.search(r"p_alias\s*=>\s*(?:nvl\([^,]+,\s*)?'([^']+)'", block)
    if m:
        meta.alias = m.group(1)

    # p_flow_language=>'pl'
    m = re.search(r"p_flow_language\s*=>\s*'([^']+)'", block)
    if m:
        meta.language = m.group(1)

    # p_flow_version=>'Release 1.0'
    m = re.search(r"p_flow_version\s*=>\s*'([^']+)'", block)
    if m:
        meta.version = m.group(1)

    # p_browser_cache=>'N'
    m = re.search(r"p_browser_cache\s*=>\s*'([^']+)'", block)
    if m:
        meta.browser_cache = m.group(1) == "Y"

    # Ustawienia istotne dla zgodności, bezpieczeństwa i wdrożenia aplikacji.
    string_settings = {
        "compatibility_mode": "p_compatibility_mode",
        "bookmark_checksum_function": "p_bookmark_checksum_function",
        "runtime_api_usage": "p_runtime_api_usage",
        "security_scheme": "p_security_scheme",
        "rejoin_existing_sessions": "p_rejoin_existing_sessions",
        "flow_status": "p_flow_status",
        "file_storage": "p_file_storage",
        "working_copy_name": "p_working_copy_name",
        "working_copy_created_by": "p_working_copy_created_by",
    }
    for attr, parameter in string_settings.items():
        m = re.search(rf"{parameter}\s*=>\s*'([^']+)'", block)
        if m:
            setattr(meta, attr, m.group(1))

    bool_settings = {
        "page_protection_enabled": "p_page_protection_enabled_y_n",
        "exact_substitutions_only": "p_exact_substitutions_only",
        "page_view_logging": "p_page_view_logging",
    }
    for attr, parameter in bool_settings.items():
        m = re.search(rf"{parameter}\s*=>\s*'([^']+)'", block)
        if m:
            setattr(meta, attr, m.group(1) in {"Y", "YES"})

    m = re.search(r"p_files_version\s*=>\s*(\d+)", block)
    if m:
        meta.files_version = int(m.group(1))

    # p_is_pwa=>'Y'
    m = re.search(r"p_is_pwa\s*=>\s*'([^']+)'", block)
    if m:
        meta.is_pwa = m.group(1) == "Y"

    # p_pwa_is_installable=>'Y'
    m = re.search(r"p_pwa_is_installable\s*=>\s*'([^']+)'", block)
    if m:
        meta.pwa_installable = m.group(1) == "Y"

    # p_pwa_is_push_enabled=>'Y'
    m = re.search(r"p_pwa_is_push_enabled\s*=>\s*'([^']+)'", block)
    if m:
        meta.push_enabled = m.group(1) == "Y"

    # Zmienne substytucyjne (p_substitution_string_XX / p_substitution_value_XX)
    sub_strings = re.findall(
        r"p_substitution_string_(\d+)\s*=>\s*'([^']+)'", block
    )
    sub_values = re.findall(
        r"p_substitution_value_(\d+)\s*=>\s*'([^']+)'", block
    )
    value_map = {num: val for num, val in sub_values}
    for num, key in sub_strings:
        if num in value_map:
            meta.substitutions[key] = value_map[num]

    # Wyciągnij copyright z substitutions
    if "APP_COPYRIGHT" in meta.substitutions:
        meta.copyright = meta.substitutions["APP_COPYRIGHT"]


def find_app_sql_file(input_dir: Path) -> Path | None:
    """Znajdź plik f*.sql w katalogu wejściowym.

    Szuka plików pasujących do wzorca f<numer>.sql (plik eksportu APEX).
    Pomija pliki zawierające 'DDL' w nazwie.
    """
    for f in input_dir.iterdir():
        if (f.is_file()
                and f.suffix.lower() == ".sql"
                and re.match(r"f\d+\.sql$", f.name, re.IGNORECASE)
                and "DDL" not in f.name.upper()):
            return f
    return None
