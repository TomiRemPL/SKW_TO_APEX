"""Modele danych APEX jako dataclasses.

Każda klasa odpowiada jednemu typowi obiektu w eksporcie APEX.
Pola odpowiadają wartościom wyekstrahowanym z plików YAML
(mapowanie YAML → model opisane w specyfikacji).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Column:
    """Kolumna w regionie (Interactive Grid/Report)."""
    name: str
    type: str                           # Link, Text, Hidden, Select...
    heading: str | None = None
    source_column: str | None = None
    data_type: str | None = None
    link_target: str | None = None      # numer strony docelowej
    lov: str | None = None
    primary_key: bool = False


@dataclass
class Region:
    """Region na stronie APEX (np. Interactive Grid, Form, Static Content)."""
    name: str
    type: str
    title: str | None = None            # tytuł widoczny dla użytkownika
    source_table: str | None = None
    source_sql: str | None = None
    parent_region: str | None = None
    columns: list[Column] = field(default_factory=list)
    editable: bool = False
    allowed_operations: list[str] = field(default_factory=list)


@dataclass
class PageItem:
    """Element formularza na stronie (pole tekstowe, lista wyboru itp.)."""
    name: str
    type: str
    label: str | None = None
    source_column: str | None = None
    lov: str | None = None
    default_value: str | None = None


@dataclass
class Process:
    """Proces serwerowy (PL/SQL, Invoke API itp.)."""
    name: str
    type: str                           # Execute Code, Invoke API...
    language: str | None = None         # PL/SQL, JavaScript
    point: str = ""                     # After Submit, Processing...
    code: str | None = None
    condition: str | None = None
    when_button_pressed: str | None = None


@dataclass
class DynamicActionStep:
    """Pojedynczy krok akcji dynamicznej."""
    type: str                           # Execute PL/SQL Code, Set Value...
    code: str | None = None
    affected_elements: str | None = None
    fire_on_initialization: bool = False


@dataclass
class DynamicAction:
    """Akcja dynamiczna (zdarzenie klienckie z reakcją)."""
    name: str
    event: str                          # Change, Click, Page Load...
    selection_type: str | None = None   # jQuery Selector, Region, Item...
    trigger_selector: str | None = None
    event_scope: str | None = None      # Dynamic, Static
    static_container: str | None = None
    actions: list[DynamicActionStep] = field(default_factory=list)


@dataclass
class Button:
    """Przycisk na stronie."""
    name: str
    label: str | None = None
    action: str | None = None           # Submit Page, Redirect...
    target_page: int | None = None
    is_hot: bool = False                # przycisk główny (primary)


@dataclass
class Branch:
    """Rozgałęzienie nawigacyjne (przekierowanie po przetworzeniu)."""
    name: str | None = None
    type: str = ""                      # Page or URL (Redirect)
    target_page: int | None = None
    target_url: str | None = None
    point: str = ""                     # After Processing
    condition: str | None = None


@dataclass
class Validation:
    """Walidacja na stronie."""
    name: str
    type: str                           # PL/SQL Function Body, Item is NOT NULL...
    code: str | None = None
    condition: str | None = None


@dataclass
class ApexPage:
    """Strona aplikacji APEX."""
    id: int
    name: str
    alias: str = ""
    title: str = ""
    page_group: str | None = None
    page_mode: str = "Normal"
    security: dict = field(default_factory=dict)
    build_options: list[str] = field(default_factory=list)
    regions: list[Region] = field(default_factory=list)
    items: list[PageItem] = field(default_factory=list)
    buttons: list[Button] = field(default_factory=list)
    processes: list[Process] = field(default_factory=list)
    dynamic_actions: list[DynamicAction] = field(default_factory=list)
    branches: list[Branch] = field(default_factory=list)
    validations: list[Validation] = field(default_factory=list)
    css_inline: str | None = None
    js_inline: str | None = None


@dataclass
class LOV:
    """Lista wartości (List of Values)."""
    name: str
    source_type: str = ""               # Table / View, SQL Query, Static Values
    source_table: str | None = None
    sql_query: str | None = None
    entries: list[dict] | None = None   # dla Static Values
    return_column: str | None = None
    display_column: str | None = None


@dataclass
class Authorization:
    """Schemat autoryzacji."""
    name: str
    type: str | None = None
    code: str | None = None             # PL/SQL function body
    role_or_group: str | None = None


@dataclass
class NavList:
    """Lista nawigacyjna (menu)."""
    name: str
    entries: list[dict] = field(default_factory=list)


@dataclass
class AppItem:
    """Zmienna globalna aplikacji (Application Item)."""
    name: str
    scope: str | None = None


@dataclass
class BuildOption:
    """Opcja budowania (Feature toggle)."""
    name: str
    status: str = ""                    # Include, Exclude


@dataclass
class Breadcrumb:
    """Ścieżka nawigacyjna (breadcrumb)."""
    name: str
    entries: list[dict] = field(default_factory=list)


@dataclass
class AclRole:
    """Rola ACL."""
    name: str
    static_id: str | None = None


@dataclass
class AppMetadata:
    """Metadane aplikacji APEX z pliku eksportu SQL (f*.sql)."""
    app_id: str = ""
    app_name: str = ""
    alias: str = ""
    version: str = ""                   # np. "Release 1.0"
    apex_version: str = ""              # np. "24.2.10"
    owner: str = ""                     # schemat (np. DAW)
    exported_by: str = ""               # kto wyeksportował
    language: str = ""                  # pl, en, ...
    # Statystyki
    pages_count: int = 0
    items_count: int = 0
    regions_count: int = 0
    buttons_count: int = 0
    processes_count: int = 0
    dynamic_actions_count: int = 0
    validations_count: int = 0
    lovs_count: int = 0
    auth_schemes_count: int = 0
    build_options_count: int = 0
    lists_count: int = 0
    # Ustawienia
    is_pwa: bool = False
    pwa_installable: bool = False
    push_enabled: bool = False
    browser_cache: bool = False
    copyright: str = ""
    substitutions: dict[str, str] = field(default_factory=dict)


@dataclass
class DDLColumn:
    """Kolumna tabeli z DDL."""
    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None
    primary_key: bool = False
    identity: bool = False
    identity_def: str | None = None  # pełna definicja GENERATED ... AS IDENTITY


@dataclass
class DDLConstraint:
    """Ograniczenie tabeli (FK, CHECK, UNIQUE)."""
    name: str
    type: str                           # PRIMARY KEY, FOREIGN KEY, CHECK, UNIQUE
    columns: list[str] = field(default_factory=list)
    ref_table: str | None = None
    ref_column: str | None = None
    check_condition: str | None = None


@dataclass
class DDLTable:
    """Tabela z DDL."""
    name: str
    columns: list[DDLColumn] = field(default_factory=list)
    constraints: list[DDLConstraint] = field(default_factory=list)
    comment: str | None = None
    column_comments: dict[str, str] = field(default_factory=dict)
    raw_sql: str | None = None  # oryginalne CREATE TABLE SQL


@dataclass
class DDLView:
    """Widok z DDL."""
    name: str
    sql: str = ""
    comment: str | None = None


@dataclass
class DDLPackage:
    """Pakiet PL/SQL z DDL."""
    name: str
    code: str = ""


@dataclass
class DDLProcedure:
    """Samodzielna procedura/funkcja PL/SQL z DDL."""
    name: str
    code: str = ""


@dataclass
class DDLSequence:
    """Sekwencja z DDL."""
    name: str
    start_with: str | None = None
    increment_by: str | None = None
    min_value: str | None = None
    max_value: str | None = None
    cache_size: str | None = None
    nocache: bool = False
    noorder: bool = False
    nocycle: bool = False
    raw_sql: str | None = None  # oryginalne CREATE SEQUENCE SQL


@dataclass
class DDLSchema:
    """Pełny schemat bazy danych wyekstrahowany z DDL."""
    tables: list[DDLTable] = field(default_factory=list)
    views: list[DDLView] = field(default_factory=list)
    packages: list[DDLPackage] = field(default_factory=list)
    procedures: list[DDLProcedure] = field(default_factory=list)
    sequences: list[DDLSequence] = field(default_factory=list)
    raw_content: str = ""  # surowa treść pliku DDL
    source_schema: str = ""  # nazwa schematu źródłowego (np. DAW)


@dataclass
class ApexApp:
    """Główny model aplikacji APEX — agregat wszystkich komponentów."""
    name: str
    id: str
    alias: str = ""
    pages: list[ApexPage] = field(default_factory=list)
    lovs: list[LOV] = field(default_factory=list)
    authorizations: list[Authorization] = field(default_factory=list)
    nav_lists: list[NavList] = field(default_factory=list)
    app_items: list[AppItem] = field(default_factory=list)
    build_options: list[BuildOption] = field(default_factory=list)
    breadcrumbs: list[Breadcrumb] = field(default_factory=list)
    acl_roles: list[AclRole] = field(default_factory=list)
    ddl_schema: DDLSchema | None = None
    metadata: AppMetadata | None = None
