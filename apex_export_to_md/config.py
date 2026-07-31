"""Konfiguracja i stałe programu.

Wszystkie przełączniki i heurystyki filtrowania w jednym miejscu.
Wartości domyślne mogą być nadpisane przez argumenty CLI.
"""
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Konfiguracja aplikacji — łączy wartości domyślne z argumentami CLI."""

    # --- Ścieżki ---
    input_dir: str = "_data"
    output_dir: str = "_out"
    output_prefix: str = "apex_export"

    # --- Plik DDL ---
    ddl_file: str = ""

    # --- Format wyjściowy ---
    # Dozwolone: "both", "human", "llm"
    output_format: str = "both"

    # --- Kod PL/SQL i JavaScript ---
    # Dozwolone: "full", "summary", "none"
    include_code: str = "full"

    # --- Filtrowanie stron ---
    # Dozwolone: "auto", "all", "prefix:<X>", "ids:<1,2,3>"
    page_filter: str = "auto"
    extra_pages: list[int] = field(default_factory=list)

    # --- Generowanie skryptów DDL/migracji ---
    generate_ddl: bool = False
    generate_migration: bool = False
    db_connection: str = ""

    # --- Automatyczne pobieranie DDL z bazy ---
    fetch_ddl_from_db: bool = False
    ddl_keyword: str = ""

    # --- GUI ---
    gui: bool = False

    # --- Raport pokrycia ---
    coverage: bool = False
    coverage_config: str = ""

    # --- Opcje dodatkowe ---
    include_internal_ids: bool = False
    include_layout: bool = False
    include_shared_components: bool = True
    verbose: bool = False


# --- Heurystyki filtrowania stron standardowych APEX ---

# Grupy stron do pominięcia (standardowe moduły APEX)
STANDARD_PAGE_GROUPS: list[str] = [
    "Administration",
    "User Settings",
]

# Schemat autoryzacji oznaczający stronę administracyjną
STANDARD_AUTH_SCHEME: str = "Administration Rights"

# Nazwy stron systemowych (zawsze pomijane w trybie auto)
SYSTEM_PAGE_NAMES: list[str] = [
    "Global Page",
    "Login Page",
]

# --- Klucze YAML do odfiltrowania (szum) ---

SKIP_YAML_KEYS: list[str] = [
    "accessibility",
    "customization",
    "server-cache",
    "session-management",
    "subscription",
    "export-/-printing",
    "column-filter",
    "enable-users-to",
    "pagination",
    "toolbar",
    "icon-view",
    "detail-view",
    "saved-reports",
    "download",
]

# Klucze zagnieżdżone do odfiltrowania (notacja z kropką)
SKIP_NESTED_KEYS: list[str] = [
    "advanced.region-display-selector",
    "advanced.exclude-title-from-translation",
    "advanced.enable-duplicate-page-submissions",
    "heading.fixed-to",
]
