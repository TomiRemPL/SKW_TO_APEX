"""Modele danych APEX jako dataclasses.

Każda klasa odpowiada jednemu typowi obiektu w eksporcie APEX.
Pola odpowiadają wartościom wyekstrahowanym z plików YAML
(mapowanie YAML → model opisane w specyfikacji).

Każdy obiekt zawiera pole `raw_attributes: dict` z pełnymi danymi YAML
(po usunięciu ID APEX i kluczy technicznych).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Column:
    """Kolumna w regionie (Interactive Grid/Report)."""
    name: str
    type: str
    heading: str | None = None
    source_column: str | None = None
    data_type: str | None = None
    link_target: str | None = None
    lov: str | None = None
    primary_key: bool = False
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class Region:
    """Region na stronie APEX (np. Interactive Grid, Form, Static Content)."""
    name: str
    type: str
    title: str | None = None
    source_table: str | None = None
    source_sql: str | None = None
    parent_region: str | None = None
    columns: list[Column] = field(default_factory=list)
    editable: bool = False
    allowed_operations: list[str] = field(default_factory=list)
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class PageItem:
    """Element formularza na stronie (pole tekstowe, lista wyboru itp.)."""
    name: str
    type: str
    label: str | None = None
    source_column: str | None = None
    lov: str | None = None
    default_value: str | None = None
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class Process:
    """Proces serwerowy (PL/SQL, Invoke API itp.)."""
    name: str
    type: str
    language: str | None = None
    point: str = ""
    code: str | None = None
    condition: str | None = None
    when_button_pressed: str | None = None
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class DynamicActionStep:
    """Pojedynczy krok akcji dynamicznej."""
    type: str
    code: str | None = None
    affected_elements: str | None = None
    fire_on_initialization: bool = False
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class DynamicAction:
    """Akcja dynamiczna (zdarzenie klienckie z reakcją)."""
    name: str
    event: str
    selection_type: str | None = None
    trigger_selector: str | None = None
    event_scope: str | None = None
    static_container: str | None = None
    actions: list[DynamicActionStep] = field(default_factory=list)
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class Button:
    """Przycisk na stronie."""
    name: str
    label: str | None = None
    action: str | None = None
    target_page: int | None = None
    is_hot: bool = False
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class Branch:
    """Rozgałęzienie nawigacyjne (przekierowanie po przetworzeniu)."""
    name: str | None = None
    type: str = ""
    target_page: int | None = None
    target_url: str | None = None
    point: str = ""
    condition: str | None = None
    raw_attributes: dict = field(default_factory=dict)


@dataclass
class Validation:
    """Walidacja na stronie."""
    name: str
    type: str
    code: str | None = None
    condition: str | None = None
    raw_attributes: dict = field(default_factory=dict)


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
    raw_attributes: dict = field(default_factory=dict)


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
