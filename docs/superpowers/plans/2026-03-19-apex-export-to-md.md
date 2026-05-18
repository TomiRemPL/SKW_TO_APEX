# APEX Export → Markdown Converter — Plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skrypt Python konwertujący eksport APEX (readable YAML) na dwa pliki Markdown — czytelny dla człowieka i zoptymalizowany dla LLM.

**Architecture:** Pipeline: YAML → Parser → dataclass model → Filter → Renderer → .md. Separacja warstw: parser, modele, filtr, renderery. Graceful degradation przy brakujących kluczach YAML.

**Tech Stack:** Python 3.10+, PyYAML, argparse, dataclasses, pytest

**Spec:** `docs/superpowers/specs/2026-03-19-apex-export-to-md-design.md`

---

## Struktura plików

```
apex_export_to_md/
├── __init__.py
├── __main__.py               # umożliwia `python -m apex_export_to_md`
├── cli.py                    # punkt wejścia CLI (argparse)
├── config.py                 # przełączniki, stałe, heurystyki
├── models/
│   ├── __init__.py
│   └── apex_models.py        # wszystkie dataclasses
├── parser/
│   ├── __init__.py
│   ├── yaml_helpers.py       # bezpieczne odczytywanie zagnieżdżonych kluczy
│   ├── page_parser.py        # parsuje pages/*.yaml
│   └── shared_parser.py      # parsuje shared_components/*.yaml
├── filters/
│   ├── __init__.py
│   └── page_filter.py        # heurystyki filtrowania stron
├── renderers/
│   ├── __init__.py
│   ├── base_renderer.py      # abstrakcyjna klasa bazowa
│   ├── human_renderer.py     # Markdown z tabelami
│   └── llm_renderer.py       # skondensowany format liniowy
tests/
├── __init__.py
├── conftest.py               # współdzielone fixtures YAML
├── test_models.py
├── test_yaml_helpers.py
├── test_page_parser.py
├── test_shared_parser.py
├── test_page_filter.py
├── test_human_renderer.py
├── test_llm_renderer.py
└── test_cli.py
```

---

### Task 1: Scaffold projektu i konfiguracja

**Files:**
- Create: `apex_export_to_md/__init__.py`
- Create: `apex_export_to_md/__main__.py`
- Create: `apex_export_to_md/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Utwórz katalogi**

```bash
mkdir -p apex_export_to_md/models apex_export_to_md/parser apex_export_to_md/filters apex_export_to_md/renderers tests
```

- [ ] **Step 2: Utwórz `apex_export_to_md/__init__.py`**

```python
"""APEX Export → Markdown Converter.

Konwertuje eksport Oracle APEX (format readable/YAML) na pliki Markdown.
"""
__version__ = "0.1.0"
```

- [ ] **Step 3: Utwórz `apex_export_to_md/__main__.py`**

```python
"""Umożliwia uruchomienie jako `python -m apex_export_to_md`."""
from apex_export_to_md.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Utwórz `apex_export_to_md/config.py`**

```python
"""Konfiguracja i stałe programu.

Wszystkie przełączniki i heurystyki filtrowania w jednym miejscu.
Wartości domyślne mogą być nadpisane przez argumenty CLI.
"""
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Konfiguracja aplikacji — łączy wartości domyślne z argumentami CLI."""

    # --- Ścieżki ---
    input_dir: str = ""
    output_dir: str = "."
    output_prefix: str = "apex_export"

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
```

- [ ] **Step 5: Utwórz `requirements.txt`**

```
PyYAML>=6.0
pytest>=7.0
```

- [ ] **Step 6: Utwórz pusty `tests/__init__.py`**

```python
```

- [ ] **Step 7: Napisz test konfiguracji**

Plik: `tests/test_config.py`

```python
"""Testy modułu konfiguracji."""
from apex_export_to_md.config import AppConfig, STANDARD_PAGE_GROUPS, SYSTEM_PAGE_NAMES


def test_domyslna_konfiguracja():
    """Sprawdza, że domyślne wartości konfiguracji są poprawne."""
    cfg = AppConfig()
    assert cfg.output_format == "both"
    assert cfg.include_code == "full"
    assert cfg.page_filter == "auto"
    assert cfg.include_shared_components is True
    assert cfg.verbose is False
    assert cfg.extra_pages == []


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
```

- [ ] **Step 8: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_config.py -v
```

Expected: 3 PASSED

- [ ] **Step 9: Commit**

```bash
git add apex_export_to_md/ tests/ requirements.txt
git commit -m "feat: scaffold projektu i moduł konfiguracji"
```

---

### Task 2: Modele danych (dataclasses)

**Files:**
- Create: `apex_export_to_md/models/__init__.py`
- Create: `apex_export_to_md/models/apex_models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Utwórz `apex_export_to_md/models/__init__.py`**

```python
"""Modele danych APEX — dataclasses reprezentujące strukturę aplikacji."""
from apex_export_to_md.models.apex_models import (
    ApexApp, ApexPage, Region, Column, PageItem, Process,
    DynamicAction, DynamicActionStep, Button, Branch, Validation,
    LOV, Authorization, NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)

__all__ = [
    "ApexApp", "ApexPage", "Region", "Column", "PageItem", "Process",
    "DynamicAction", "DynamicActionStep", "Button", "Branch", "Validation",
    "LOV", "Authorization", "NavList", "AppItem", "BuildOption", "Breadcrumb", "AclRole",
]
```

- [ ] **Step 2: Utwórz `apex_export_to_md/models/apex_models.py`**

```python
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
```

- [ ] **Step 3: Napisz testy modeli**

Plik: `tests/test_models.py`

```python
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
```

- [ ] **Step 4: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_models.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/models/ tests/test_models.py
git commit -m "feat: modele danych APEX (dataclasses)"
```

---

### Task 3: Helpery YAML (bezpieczne odczytywanie zagnieżdżonych kluczy)

**Files:**
- Create: `apex_export_to_md/parser/__init__.py`
- Create: `apex_export_to_md/parser/yaml_helpers.py`
- Create: `tests/test_yaml_helpers.py`

- [ ] **Step 1: Utwórz `apex_export_to_md/parser/__init__.py`**

```python
"""Parsery plików YAML eksportu APEX."""
```

- [ ] **Step 2: Napisz testy helperów**

Plik: `tests/test_yaml_helpers.py`

```python
"""Testy helperów do bezpiecznego odczytu YAML."""
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_int, safe_get_bool, safe_get_list,
    strip_apex_id, collect_build_options,
)


def test_safe_get_klucz_prosty():
    data = {"name": "test"}
    assert safe_get(data, "name") == "test"


def test_safe_get_klucz_zagniezdony():
    data = {"identification": {"name": "Foo", "title": "Bar"}}
    assert safe_get(data, "identification.name") == "Foo"
    assert safe_get(data, "identification.title") == "Bar"


def test_safe_get_brakujacy_klucz():
    data = {"a": {"b": 1}}
    assert safe_get(data, "a.c") is None
    assert safe_get(data, "x.y.z") is None
    assert safe_get(data, "a.c", "default") == "default"


def test_safe_get_str_obcina_id_apex():
    """Tekst z komentarzem ID APEX (np. 'Administration # 123456') → 'Administration'."""
    data = {"page-group": "Administration # 52840988022029242"}
    assert safe_get_str(data, "page-group", strip_id=True) == "Administration"


def test_safe_get_str_bez_obcinania():
    data = {"page-group": "Administration # 52840988022029242"}
    assert safe_get_str(data, "page-group", strip_id=False) == "Administration # 52840988022029242"


def test_safe_get_int():
    data = {"id": 42}
    assert safe_get_int(data, "id") == 42
    assert safe_get_int(data, "missing", 0) == 0


def test_safe_get_bool():
    data = {"edit": {"enabled": True}}
    assert safe_get_bool(data, "edit.enabled") is True
    assert safe_get_bool(data, "edit.missing") is False


def test_safe_get_list():
    data = {"ops": ["Add", "Delete"]}
    assert safe_get_list(data, "ops") == ["Add", "Delete"]
    assert safe_get_list(data, "missing") == []


def test_strip_apex_id():
    assert strip_apex_id("Foo # 123456789") == "Foo"
    assert strip_apex_id("Foo") == "Foo"
    assert strip_apex_id(None) is None


def test_collect_build_options():
    """Zbiera wszystkie build-option z zagnieżdżonej struktury."""
    data = {
        "build-option": "Feature: X # 123",
        "regions": [
            {"build-option": "Commented Out # 456"},
            {"nested": {"build-option": "Feature: Y # 789"}},
        ],
    }
    result = collect_build_options(data)
    assert "Feature: X" in result
    assert "Commented Out" in result
    assert "Feature: Y" in result
```

- [ ] **Step 3: Zaimplementuj helpery**

Plik: `apex_export_to_md/parser/yaml_helpers.py`

```python
"""Helpery do bezpiecznego odczytu zagnieżdżonych struktur YAML.

Eksport APEX używa głęboko zagnieżdżonych kluczy (np. identification.name,
source.table-name). Te funkcje zapobiegają KeyError/TypeError przy brakujących
kluczach i zapewniają spójne domyślne wartości.
"""
from __future__ import annotations
import re
from typing import Any


def safe_get(data: dict | None, key_path: str, default: Any = None) -> Any:
    """Bezpieczne odczytanie wartości z zagnieżdżonego słownika.

    Args:
        data: Słownik źródłowy (może być None)
        key_path: Ścieżka klucza z kropkami, np. "identification.name"
        default: Wartość domyślna gdy klucz nie istnieje

    Returns:
        Wartość pod podaną ścieżką lub default
    """
    if data is None:
        return default

    keys = key_path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def safe_get_str(
    data: dict | None,
    key_path: str,
    default: str | None = None,
    strip_id: bool = True,
) -> str | None:
    """Odczytaj wartość tekstową, opcjonalnie usuwając sufiks ID APEX.

    Wiele wartości YAML zawiera komentarz z ID, np.:
        'Administration # 52840988022029242'
    Parametr strip_id=True obcina ten sufiks.
    """
    value = safe_get(data, key_path, default)
    if value is None:
        return default
    value = str(value)
    if strip_id:
        value = strip_apex_id(value)
    return value


def safe_get_int(data: dict | None, key_path: str, default: int = 0) -> int:
    """Odczytaj wartość całkowitą."""
    value = safe_get(data, key_path)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_get_bool(data: dict | None, key_path: str, default: bool = False) -> bool:
    """Odczytaj wartość logiczną."""
    value = safe_get(data, key_path)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1")
    return default


def safe_get_list(data: dict | None, key_path: str) -> list:
    """Odczytaj listę (pustą gdy brak klucza)."""
    value = safe_get(data, key_path)
    if isinstance(value, list):
        return value
    return []


# Wzorzec: tekst, opcjonalnie zakończony " # <cyfry>"
_APEX_ID_SUFFIX = re.compile(r"\s*#\s*\d{10,}\s*$")


def strip_apex_id(value: str | None) -> str | None:
    """Usuń sufiks ID APEX z tekstu, np. 'Foo # 123456' → 'Foo'."""
    if value is None:
        return None
    return _APEX_ID_SUFFIX.sub("", value).strip()


def collect_build_options(data: dict) -> list[str]:
    """Zbierz rekurencyjnie wszystkie wartości klucza 'build-option' ze struktury.

    Zwraca listę nazw build-options (z obciętymi ID APEX).
    """
    results: list[str] = []
    _collect_bo_recursive(data, results)
    return results


def _collect_bo_recursive(obj: Any, results: list[str]) -> None:
    """Rekurencyjne przeszukiwanie struktury w poszukiwaniu 'build-option'."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "build-option" and isinstance(value, str):
                cleaned = strip_apex_id(value)
                if cleaned and cleaned not in results:
                    results.append(cleaned)
            else:
                _collect_bo_recursive(value, results)
    elif isinstance(obj, list):
        for item in obj:
            _collect_bo_recursive(item, results)
```

- [ ] **Step 4: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_yaml_helpers.py -v
```

Expected: 10 PASSED

- [ ] **Step 5: Commit**

```bash
git add apex_export_to_md/parser/ tests/test_yaml_helpers.py
git commit -m "feat: helpery YAML (bezpieczne zagnieżdżone odczyty)"
```

---

### Task 4: Fixtures testowe (przykładowe dane YAML)

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Utwórz fixtures**

Plik: `tests/conftest.py`

```python
"""Współdzielone fixtures — przykładowe struktury YAML eksportu APEX."""
import pytest


@pytest.fixture
def sample_page_yaml() -> dict:
    """Minimalna strona użytkownika (wzór: DAW_LISTA_AUDYTOW)."""
    return {
        "id": 4,
        "identification": {
            "name": "DAW_LISTA_AUDYTOW",
            "alias": "DAW-LISTA-AUDYTOW",
            "title": "DAW_LISTA_AUDYTOW",
        },
        "appearance": {"page-mode": "Normal"},
        "security": {
            "authentication": "Page Requires Authentication",
            "page-access-protection": "Arguments Must Have Checksum",
        },
        "css": {"inline": ".highlight { color: red; }"},
        "regions": [
            {
                "identification": {
                    "name": "ListaAudytow",
                    "title": "Lista audytów",
                    "type": "Interactive Grid",
                },
                "source": {
                    "location": "Local Database",
                    "type": "Table / View",
                    "table-name": "B_AUDYT",
                },
                "layout": {
                    "sequence": 20,
                    "parent-region": "No Parent",
                    "slot": "BODY",
                },
                "attributes": {
                    "edit": {
                        "enabled": True,
                        "allowed-operations": ["Add Row", "Update Row", "Delete Row"],
                    },
                },
                "columns": [
                    {
                        "identification": {"column-name": "ID_PK_B_AUDYT", "type": "Hidden"},
                        "source": {
                            "database-column": "ID_PK_B_AUDYT",
                            "data-type": "NUMBER",
                            "primary-key": True,
                        },
                    },
                    {
                        "identification": {"column-name": "B_AUDYT_NUMER_AUDYTU", "type": "Link"},
                        "heading": {"heading": "Numer Audytu"},
                        "source": {
                            "database-column": "B_AUDYT_NUMER_AUDYTU",
                            "data-type": "VARCHAR2",
                            "primary-key": False,
                        },
                        "link": {"target": {"page": "6 # DAW_WYBOR_KONTROLI"}},
                    },
                ],
            },
        ],
        "page-items": [
            {
                "identification": {"name": "P4_FILTR_STATUS", "type": "Select List"},
                "label": {"label": "Status"},
                "list-of-values": {"list-of-values": "STATUS_AUDYTU # 123"},
                "source": {"type": "Null"},
            },
        ],
        "buttons": [
            {
                "identification": {"button-name": "UTWORZ_AUDYT"},
                "label": {"label": "Nowy audyt"},
                "behavior": {"action": "Submit Page"},
                "appearance": {"hot": True},
            },
        ],
        "processes": [
            {
                "identification": {"name": "Zapisz_Dane", "type": "Execute Code"},
                "source": {
                    "language": "PL/SQL",
                    "pl/sql-code": "BEGIN PKG_AUDYT.ZAPISZ(:P4_ID); END;",
                },
                "execution": {"point": "After Submit"},
                "server-side-condition": {"when-button-pressed": "SAVE # 999"},
            },
        ],
        "dynamic-actions": [
            {
                "identification": {"name": "Zmiana_statusu"},
                "when": {
                    "event": "Change",
                    "selection-type": "Item",
                    "item": "P4_STATUS",
                },
                "execution": {"event-scope": "Dynamic"},
                "actions": [
                    {
                        "identification": {"action": "Execute PL/SQL Code"},
                        "settings": {"pl/sql-code": "BEGIN NULL; END;"},
                        "affected-elements": {
                            "selection-type": "jQuery Selector",
                            "jquery-selector": "#region1",
                        },
                        "execution": {"fire-on-initialization": False},
                    },
                ],
            },
        ],
        "branches": [
            {
                "identification": {"name": "Go To Page 6"},
                "behavior": {
                    "type": "Page or URL (Redirect)",
                    "target": {"page": "6 # DAW_WYBOR_KONTROLI", "url": None},
                },
                "execution": {"point": "After Processing"},
                "server-side-condition": {"type": "Request = Value", "value": "SAVE"},
            },
        ],
        "validations": [
            {
                "identification": {"name": "Sprawdz_Numer"},
                "validation": {
                    "type": "PL/SQL Function Body",
                    "pl/sql-function-body": "RETURN :P4_NUMER IS NOT NULL;",
                },
            },
        ],
    }


@pytest.fixture
def sample_admin_page_yaml() -> dict:
    """Strona administracyjna (powinna być odfiltrowana)."""
    return {
        "id": 10000,
        "identification": {
            "name": "Administration",
            "alias": "ADMIN",
            "title": "Administration",
            "page-group": "Administration # 52840988022029242",
        },
        "appearance": {"page-mode": "Normal"},
        "security": {
            "authorization-scheme": "Administration Rights # 52839508229029280",
            "authentication": "Page Requires Authentication",
        },
    }


@pytest.fixture
def sample_lovs_yaml() -> list[dict]:
    """Przykładowe LOV-y trzech typów."""
    return [
        {
            "identification": {"name": "B_AUDYT.NUMER"},
            "source": {"type": "Table / View", "table-name": "B_AUDYT"},
            "column-mapping": {"return": "ID_PK_B_AUDYT", "display": "B_AUDYT_NUMER_AUDYTU"},
        },
        {
            "identification": {"name": "KONTROLE_SQL"},
            "source": {
                "type": "SQL Query",
                "sql-query": "SELECT id, name FROM B_KONTROLA WHERE active = 1",
            },
            "column-mapping": {"return": "id", "display": "name"},
        },
        {
            "identification": {"name": "TAK_NIE"},
            "source": {"type": "Static Values"},
            "entries": [
                {"entry": {"sequence": 1, "display": "Tak", "return": "1"}},
                {"entry": {"sequence": 2, "display": "Nie", "return": "0"}},
            ],
        },
    ]


@pytest.fixture
def sample_app_yaml() -> dict:
    """Główny plik aplikacji (f338.yaml)."""
    return {
        "id": 160,
        "identification": {"name": "SKW_2_APEX", "alias": "START338"},
    }


@pytest.fixture
def sample_authorizations_yaml() -> list[dict]:
    """Schematy autoryzacji."""
    return [
        {
            "identification": {"name": "AD Role"},
            "authorization-scheme": {"type": "PL/SQL Function Returning Boolean"},
            "settings": {"pl/sql-function-body": "RETURN TRUE;"},
        },
        {
            "identification": {"name": "Administration Rights"},
            "authorization-scheme": {"type": "Is In Role or Group"},
            "settings": {"type": "Application Role", "name(s)": "Administrator"},
        },
    ]
```

- [ ] **Step 2: Sprawdź, że fixtures się importują**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_models.py -v
```

Expected: 6 PASSED (poprzednie testy nadal działają)

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "feat: fixtures testowe (przykładowe dane YAML)"
```

---

### Task 5: Parser stron (page_parser.py)

**Files:**
- Create: `apex_export_to_md/parser/page_parser.py`
- Create: `tests/test_page_parser.py`

- [ ] **Step 1: Napisz testy parsera stron**

Plik: `tests/test_page_parser.py`

```python
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
```

- [ ] **Step 2: Zaimplementuj parser stron**

Plik: `apex_export_to_md/parser/page_parser.py`

```python
"""Parser stron APEX (pages/*.yaml).

Czyta pliki YAML i konwertuje je na obiekty ApexPage z pełną strukturą:
regiony, kolumny, elementy, przyciski, procesy, DA, branches, walidacje.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

import yaml

from apex_export_to_md.models import (
    ApexPage, Region, Column, PageItem, Process,
    DynamicAction, DynamicActionStep, Button, Branch, Validation,
)
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_int, safe_get_bool, safe_get_list,
    collect_build_options,
)

logger = logging.getLogger(__name__)


def parse_all_pages(pages_dir: Path) -> list[ApexPage]:
    """Parsuj wszystkie pliki stron z katalogu pages/.

    Args:
        pages_dir: Ścieżka do katalogu pages/

    Returns:
        Lista sparsowanych stron, posortowana po ID
    """
    pages: list[ApexPage] = []
    if not pages_dir.exists():
        logger.warning("Katalog stron nie istnieje: %s", pages_dir)
        return pages

    for yaml_file in sorted(pages_dir.glob("p*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                page = parse_page(data)
                pages.append(page)
                logger.debug("Sparsowano stronę: %s (ID=%d)", page.name, page.id)
        except Exception as e:
            logger.warning("Błąd parsowania %s: %s", yaml_file.name, e)

    return sorted(pages, key=lambda p: p.id)


def parse_page(data: dict) -> ApexPage:
    """Parsuj pojedynczą stronę APEX z danych YAML.

    Args:
        data: Słownik z załadowanego pliku YAML strony

    Returns:
        Obiekt ApexPage z wypełnionymi polami
    """
    ident = data.get("identification", {})

    # Parsowanie page-group — może być w identification lub na poziomie top-level
    page_group = safe_get_str(ident, "page-group", strip_id=True)

    return ApexPage(
        id=safe_get_int(data, "id"),
        name=safe_get_str(ident, "name", "") or "",
        alias=safe_get_str(ident, "alias", "") or "",
        title=safe_get_str(ident, "title", "") or "",
        page_group=page_group,
        page_mode=safe_get_str(data, "appearance.page-mode", "Normal") or "Normal",
        security=data.get("security", {}),
        build_options=collect_build_options(data),
        regions=_parse_regions(data.get("regions", [])),
        items=_parse_items(data.get("page-items", [])),
        buttons=_parse_buttons(data.get("buttons", [])),
        processes=_parse_processes(data.get("processes", [])),
        dynamic_actions=_parse_dynamic_actions(data.get("dynamic-actions", [])),
        branches=_parse_branches(data.get("branches", [])),
        validations=_parse_validations(data.get("validations", [])),
        css_inline=safe_get(data, "css.inline"),
        js_inline=(
            safe_get(data, "javascript.execute-when-page-loads")
            or safe_get(data, "javascript.inline")
        ),
    )


# --- Parsery podrzędne ---


def _parse_regions(regions_data: list[dict]) -> list[Region]:
    """Parsuj listę regionów."""
    regions: list[Region] = []
    for r in regions_data or []:
        ident = r.get("identification", {})
        source = r.get("source", {})
        attrs = r.get("attributes", {})
        edit = attrs.get("edit", {})

        region = Region(
            name=safe_get_str(ident, "name", "") or "",
            title=safe_get_str(ident, "title"),
            type=safe_get_str(ident, "type", "") or "",
            source_table=safe_get_str(source, "table-name"),
            source_sql=safe_get(source, "sql-query"),
            parent_region=_clean_parent_region(safe_get_str(r, "layout.parent-region")),
            columns=_parse_columns(r.get("columns", [])),
            editable=safe_get_bool(edit, "enabled") if isinstance(edit, dict) else False,
            allowed_operations=safe_get_list(edit, "allowed-operations") if isinstance(edit, dict) else [],
        )
        regions.append(region)
    return regions


def _clean_parent_region(value: str | None) -> str | None:
    """Zamień 'No Parent' na None."""
    if value and value.strip().lower() == "no parent":
        return None
    return value


def _parse_columns(columns_data: list[dict]) -> list[Column]:
    """Parsuj listę kolumn regionu."""
    columns: list[Column] = []
    for c in columns_data or []:
        ident = c.get("identification", {})
        source = c.get("source", {})
        link = c.get("link", {})
        link_target_raw = safe_get(link, "target.page")

        # Wyciągnij numer strony z formatu "6 # DAW_WYBOR_KONTROLI"
        link_target = None
        if link_target_raw:
            link_str = str(link_target_raw).split("#")[0].strip()
            try:
                link_target = str(int(link_str))
            except ValueError:
                link_target = link_str

        column = Column(
            name=safe_get_str(ident, "column-name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            heading=safe_get_str(c, "heading.heading"),
            source_column=safe_get_str(source, "database-column"),
            data_type=safe_get_str(source, "data-type"),
            link_target=link_target,
            lov=safe_get_str(c, "list-of-values.list-of-values", strip_id=True),
            primary_key=safe_get_bool(source, "primary-key"),
        )
        columns.append(column)
    return columns


def _parse_items(items_data: list[dict]) -> list[PageItem]:
    """Parsuj elementy formularza strony."""
    items: list[PageItem] = []
    for item_data in items_data or []:
        ident = item_data.get("identification", {})
        source = item_data.get("source", {})

        # source_column tylko gdy typ źródła = Database Column
        source_type = safe_get_str(source, "type", "")
        source_column = None
        if source_type and "database" in source_type.lower():
            source_column = safe_get_str(source, "database-column")

        item = PageItem(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            label=safe_get_str(item_data, "label.label"),
            source_column=source_column,
            lov=safe_get_str(item_data, "list-of-values.list-of-values", strip_id=True),
            default_value=safe_get_str(item_data, "default.static-value"),
        )
        items.append(item)
    return items


def _parse_buttons(buttons_data: list[dict]) -> list[Button]:
    """Parsuj przyciski strony."""
    buttons: list[Button] = []
    for b in buttons_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})

        # Wyciągnij target page z behavior.target (jeśli redirect)
        target_page = None
        target = behavior.get("target")
        if isinstance(target, dict):
            page_raw = target.get("page")
            if page_raw:
                try:
                    target_page = int(str(page_raw).split("#")[0].strip())
                except ValueError:
                    pass

        button = Button(
            name=safe_get_str(ident, "button-name", "") or "",
            label=safe_get_str(b, "label.label"),
            action=safe_get_str(behavior, "action") if isinstance(behavior, dict) else None,
            target_page=target_page,
            is_hot=safe_get_bool(b, "appearance.hot"),
        )
        buttons.append(button)
    return buttons


def _parse_processes(processes_data: list[dict]) -> list[Process]:
    """Parsuj procesy strony."""
    processes: list[Process] = []
    for p in processes_data or []:
        ident = p.get("identification", {})
        source = p.get("source", {})
        proc_type = safe_get_str(ident, "type", "") or ""

        # Kod — zależnie od typu procesu
        code = (
            safe_get(source, "pl/sql-code")
            or safe_get(source, "javascript-code")
        )

        # Procesy typu Invoke API — złóż opis z settings
        if not code and "invoke" in proc_type.lower():
            settings = p.get("settings", {})
            pkg = safe_get_str(settings, "package")
            proc = safe_get_str(settings, "procedure-or-function")
            if pkg or proc:
                code = f"INVOKE: {pkg or '?'}.{proc or '?'}"

        # Condition — cały blok server-side-condition jako string
        ssc = p.get("server-side-condition", {})
        condition = None
        btn_pressed = None
        if isinstance(ssc, dict):
            btn_pressed = safe_get_str(ssc, "when-button-pressed", strip_id=True)
            # Zbuduj opis warunku z pozostałych kluczy
            cond_parts = []
            for key in ("type", "value", "expression"):
                val = ssc.get(key)
                if val:
                    cond_parts.append(f"{key}={val}")
            if cond_parts:
                condition = ", ".join(cond_parts)

        process = Process(
            name=safe_get_str(ident, "name", "") or "",
            type=proc_type,
            language=safe_get_str(source, "language"),
            point=safe_get_str(p, "execution.point", "") or "",
            code=code,
            condition=condition,
            when_button_pressed=btn_pressed,
        )
        processes.append(process)
    return processes


def _parse_dynamic_actions(da_data: list[dict]) -> list[DynamicAction]:
    """Parsuj akcje dynamiczne z listą kroków."""
    dynamic_actions: list[DynamicAction] = []
    for da in da_data or []:
        ident = da.get("identification", {})
        when = da.get("when", {})

        # Trigger selector — próbuj kolejno: item, jquery-selector, region, button
        trigger = (
            safe_get(when, "item")
            or safe_get(when, "jquery-selector")
            or safe_get(when, "region")
            or safe_get(when, "button")
        )

        action = DynamicAction(
            name=safe_get_str(ident, "name", "") or "",
            event=safe_get_str(when, "event", "") or "",
            selection_type=safe_get_str(when, "selection-type"),
            trigger_selector=trigger,
            event_scope=safe_get_str(da, "execution.event-scope"),
            static_container=safe_get(da, "execution.static-container-(jquery-selector)"),
            actions=_parse_da_steps(da.get("actions", [])),
        )
        dynamic_actions.append(action)
    return dynamic_actions


def _parse_da_steps(steps_data: list[dict]) -> list[DynamicActionStep]:
    """Parsuj kroki akcji dynamicznej."""
    steps: list[DynamicActionStep] = []
    for s in steps_data or []:
        ident = s.get("identification", {})
        settings = s.get("settings", {})
        affected = s.get("affected-elements", {})

        # Kod z settings
        code = (
            safe_get(settings, "pl/sql-code")
            or safe_get(settings, "javascript-code")
        )

        # Affected elements — typ selekcji + selektor
        ae_type = safe_get_str(affected, "selection-type") if isinstance(affected, dict) else None
        ae_selector = (
            safe_get(affected, "jquery-selector")
            or safe_get(affected, "item")
            or safe_get(affected, "region")
        ) if isinstance(affected, dict) else None

        affected_str = None
        if ae_type and ae_selector:
            affected_str = f"{ae_type}: {ae_selector}"
        elif ae_selector:
            affected_str = str(ae_selector)

        step = DynamicActionStep(
            type=safe_get_str(ident, "action", "") or "",
            code=code,
            affected_elements=affected_str,
            fire_on_initialization=safe_get_bool(s, "execution.fire-on-initialization"),
        )
        steps.append(step)
    return steps


def _parse_branches(branches_data: list[dict]) -> list[Branch]:
    """Parsuj rozgałęzienia nawigacyjne."""
    branches: list[Branch] = []
    for b in branches_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})
        target = behavior.get("target", {}) if isinstance(behavior, dict) else {}

        # Numer strony docelowej
        target_page = None
        page_raw = safe_get(target, "page") if isinstance(target, dict) else None
        if page_raw:
            try:
                target_page = int(str(page_raw).split("#")[0].strip())
            except ValueError:
                pass

        # Condition — filtruj kluczowe pola (analogicznie do procesów)
        ssc = b.get("server-side-condition", {})
        condition = None
        if isinstance(ssc, dict) and ssc:
            cond_parts = []
            for key in ("type", "value", "expression"):
                val = ssc.get(key)
                if val:
                    cond_parts.append(f"{key}={val}")
            if cond_parts:
                condition = ", ".join(cond_parts)

        branch = Branch(
            name=safe_get_str(ident, "name"),
            type=safe_get_str(behavior, "type", "") or "" if isinstance(behavior, dict) else "",
            target_page=target_page,
            target_url=safe_get(target, "url") if isinstance(target, dict) else None,
            point=safe_get_str(b, "execution.point", "") or "",
            condition=condition,
        )
        branches.append(branch)
    return branches


def _parse_validations(validations_data: list[dict]) -> list[Validation]:
    """Parsuj walidacje strony."""
    validations: list[Validation] = []
    for v in validations_data or []:
        ident = v.get("identification", {})
        val_block = v.get("validation", {})

        # Condition
        ssc = v.get("server-side-condition", {})
        condition = None
        if isinstance(ssc, dict) and ssc:
            cond_parts = [f"{k}={v_}" for k, v_ in ssc.items() if v_]
            if cond_parts:
                condition = ", ".join(cond_parts)

        validation = Validation(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(val_block, "type", "") or "",
            code=safe_get(val_block, "pl/sql-function-body"),
            condition=condition,
        )
        validations.append(validation)
    return validations
```

- [ ] **Step 3: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_page_parser.py -v
```

Expected: 12 PASSED

- [ ] **Step 4: Commit**

```bash
git add apex_export_to_md/parser/page_parser.py tests/test_page_parser.py
git commit -m "feat: parser stron APEX (regions, columns, items, processes, DA, branches)"
```

---

### Task 6: Parser shared components

**Files:**
- Create: `apex_export_to_md/parser/shared_parser.py`
- Create: `tests/test_shared_parser.py`

- [ ] **Step 1: Napisz testy**

Plik: `tests/test_shared_parser.py`

```python
"""Testy parsera shared components."""
from apex_export_to_md.parser.shared_parser import (
    parse_lovs, parse_authorizations, parse_app_items,
    parse_build_options, parse_breadcrumbs, parse_acl_roles, parse_nav_lists,
    parse_app_definition,
)


def test_parse_lovs_table(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert len(lovs) == 3
    assert lovs[0].source_type == "Table / View"
    assert lovs[0].source_table == "B_AUDYT"
    assert lovs[0].return_column == "ID_PK_B_AUDYT"


def test_parse_lovs_sql(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert lovs[1].source_type == "SQL Query"
    assert "B_KONTROLA" in lovs[1].sql_query


def test_parse_lovs_static(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert lovs[2].source_type == "Static Values"
    assert len(lovs[2].entries) == 2
    assert lovs[2].entries[0]["display"] == "Tak"


def test_parse_authorizations(sample_authorizations_yaml):
    auths = parse_authorizations(sample_authorizations_yaml)
    assert len(auths) == 2
    assert auths[0].type == "PL/SQL Function Returning Boolean"
    assert auths[0].code == "RETURN TRUE;"
    assert auths[1].type == "Is In Role or Group"
    assert auths[1].role_or_group == "Administrator"


def test_parse_app_definition(sample_app_yaml):
    name, app_id, alias = parse_app_definition(sample_app_yaml)
    assert name == "SKW_2_APEX"
    assert app_id == "160"
    assert alias == "START338"
```

- [ ] **Step 2: Zaimplementuj parser shared components**

Plik: `apex_export_to_md/parser/shared_parser.py`

```python
"""Parser shared components (LOVs, autoryzacje, listy, breadcrumbs, itp.).

Czyta pliki YAML z katalogu shared_components/ i konwertuje na modele.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

import yaml

from apex_export_to_md.models import (
    LOV, Authorization, NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)
from apex_export_to_md.parser.yaml_helpers import safe_get, safe_get_str

logger = logging.getLogger(__name__)


def load_yaml_file(path: Path) -> Any:
    """Bezpieczne wczytanie pliku YAML."""
    if not path.exists():
        logger.debug("Plik nie istnieje, pomijam: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Błąd wczytywania %s: %s", path.name, e)
        return None


def parse_app_definition(data: dict) -> tuple[str, str, str]:
    """Wyciągnij nazwę, ID i alias aplikacji z f*.yaml.

    Returns:
        Tuple (name, id, alias)
    """
    ident = data.get("identification", {})
    return (
        safe_get_str(ident, "name", "") or "",
        str(data.get("id", "")),
        safe_get_str(ident, "alias", "") or "",
    )


def parse_lovs(data: list[dict] | None) -> list[LOV]:
    """Parsuj listy wartości (LOV) — trzy typy: Table, SQL Query, Static Values."""
    if not data:
        return []
    lovs: list[LOV] = []
    for item in data:
        ident = item.get("identification", {})
        source = item.get("source", {})
        source_type = safe_get_str(source, "type", "") or ""
        col_mapping = item.get("column-mapping", {})

        # Dla Static Values — wyciągnij wpisy
        entries = None
        if "static" in source_type.lower():
            raw_entries = item.get("entries", [])
            entries = []
            for e in raw_entries:
                entry_data = e.get("entry", e)
                entries.append({
                    "display": entry_data.get("display", ""),
                    "return": entry_data.get("return", ""),
                })

        lov = LOV(
            name=safe_get_str(ident, "name", "") or "",
            source_type=source_type,
            source_table=safe_get_str(source, "table-name"),
            sql_query=safe_get(source, "sql-query"),
            entries=entries,
            return_column=safe_get_str(col_mapping, "return"),
            display_column=safe_get_str(col_mapping, "display"),
        )
        lovs.append(lov)
    return lovs


def parse_authorizations(data: list[dict] | None) -> list[Authorization]:
    """Parsuj schematy autoryzacji."""
    if not data:
        return []
    auths: list[Authorization] = []
    for item in data:
        ident = item.get("identification", {})
        scheme = item.get("authorization-scheme", {})
        settings = item.get("settings", {})

        auth = Authorization(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(scheme, "type"),
            code=safe_get(settings, "pl/sql-function-body"),
            role_or_group=safe_get(settings, "name(s)"),
        )
        auths.append(auth)
    return auths


def parse_nav_lists(data: list[dict] | None) -> list[NavList]:
    """Parsuj listy nawigacyjne."""
    if not data:
        return []
    nav_lists: list[NavList] = []
    for item in data:
        ident = item.get("identification", {})
        raw_entries = item.get("entries", [])
        entries: list[dict] = []
        for e in raw_entries:
            label_block = e.get("label", {})
            link = e.get("link", {})
            target = link.get("target", {}) if isinstance(link, dict) else {}
            entries.append({
                "label": safe_get_str(label_block, "label") if isinstance(label_block, dict) else None,
                "target_page": safe_get(target, "page") if isinstance(target, dict) else None,
                "parent": safe_get_str(e.get("identification", {}), "parent-entry", strip_id=True),
            })
        nav_list = NavList(
            name=safe_get_str(ident, "name", "") or "",
            entries=entries,
        )
        nav_lists.append(nav_list)
    return nav_lists


def parse_app_items(data: list[dict] | None) -> list[AppItem]:
    """Parsuj zmienne globalne aplikacji."""
    if not data:
        return []
    items: list[AppItem] = []
    for item in data:
        ident = item.get("identification", {})
        items.append(AppItem(
            name=safe_get_str(ident, "name", "") or "",
            scope=safe_get_str(ident, "scope"),
        ))
    return items


def parse_build_options(data: list[dict] | None) -> list[BuildOption]:
    """Parsuj opcje budowania (feature toggles)."""
    if not data:
        return []
    options: list[BuildOption] = []
    for item in data:
        ident = item.get("identification", {})
        status_block = item.get("status", {})
        options.append(BuildOption(
            name=safe_get_str(ident, "name", "") or "",
            status=safe_get_str(status_block, "status", "") or "",
        ))
    return options


def parse_breadcrumbs(data: list[dict] | None) -> list[Breadcrumb]:
    """Parsuj ścieżki nawigacyjne."""
    if not data:
        return []
    breadcrumbs: list[Breadcrumb] = []
    for item in data:
        ident = item.get("identification", {})
        raw_entries = item.get("entries", [])
        entries: list[dict] = []
        for e in raw_entries:
            e_ident = e.get("identification", {})
            link = e.get("link", {})
            target = link.get("target", {}) if isinstance(link, dict) else {}
            entries.append({
                "name": safe_get_str(e_ident, "name"),
                "page_number": safe_get(e_ident, "page-number"),
                "target_page": safe_get(target, "page"),
            })
        breadcrumbs.append(Breadcrumb(
            name=safe_get_str(ident, "name", "") or "",
            entries=entries,
        ))
    return breadcrumbs


def parse_acl_roles(data: list[dict] | None) -> list[AclRole]:
    """Parsuj role ACL."""
    if not data:
        return []
    roles: list[AclRole] = []
    for item in data:
        ident = item.get("identification", {})
        roles.append(AclRole(
            name=safe_get_str(ident, "name", "") or "",
            static_id=safe_get_str(item, "advanced.static-id"),
        ))
    return roles


def parse_shared_components(shared_dir: Path) -> dict:
    """Parsuj wszystkie shared components z katalogu.

    Returns:
        Słownik z kluczami: lovs, authorizations, nav_lists,
        app_items, build_options, breadcrumbs, acl_roles
    """
    result = {
        "lovs": [],
        "authorizations": [],
        "nav_lists": [],
        "app_items": [],
        "build_options": [],
        "breadcrumbs": [],
        "acl_roles": [],
    }

    if not shared_dir.exists():
        logger.warning("Katalog shared_components nie istnieje: %s", shared_dir)
        return result

    # Mapowanie: nazwa pliku → (funkcja parsująca, klucz wyniku)
    parsers = {
        "lovs.yaml": (parse_lovs, "lovs"),
        "authorizations.yaml": (parse_authorizations, "authorizations"),
        "lists.yaml": (parse_nav_lists, "nav_lists"),
        "app_items.yaml": (parse_app_items, "app_items"),
        "build_options.yaml": (parse_build_options, "build_options"),
        "breadcrumbs.yaml": (parse_breadcrumbs, "breadcrumbs"),
        "acl_roles.yaml": (parse_acl_roles, "acl_roles"),
    }

    for filename, (parser_fn, result_key) in parsers.items():
        data = load_yaml_file(shared_dir / filename)
        if data:
            result[result_key] = parser_fn(data)
            logger.debug("Sparsowano %s: %d elementów", filename, len(result[result_key]))

    return result
```

- [ ] **Step 3: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_shared_parser.py -v
```

Expected: 5 PASSED

- [ ] **Step 4: Commit**

```bash
git add apex_export_to_md/parser/shared_parser.py tests/test_shared_parser.py
git commit -m "feat: parser shared components (LOVs, autoryzacje, nawigacja, ACL)"
```

---

### Task 7: Filtr stron

**Files:**
- Create: `apex_export_to_md/filters/__init__.py`
- Create: `apex_export_to_md/filters/page_filter.py`
- Create: `tests/test_page_filter.py`

- [ ] **Step 1: Napisz testy filtra**

Plik: `tests/test_page_filter.py`

```python
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
```

- [ ] **Step 2: Zaimplementuj filtr**

Plik: `apex_export_to_md/filters/__init__.py`

```python
"""Filtry stron APEX."""
```

Plik: `apex_export_to_md/filters/page_filter.py`

```python
"""Filtr stron APEX — heurystyki do rozróżnienia stron użytkownika od standardowych.

Tryby filtrowania:
  - auto: heurystyki (page-group, authorization-scheme, nazwa systemowa)
  - all: brak filtrowania
  - prefix:<X>: filtr po prefiksie nazwy strony
  - ids:<1,2,3>: filtr po konkretnych ID stron
"""
from __future__ import annotations
import logging
from apex_export_to_md.config import (
    AppConfig, STANDARD_PAGE_GROUPS, STANDARD_AUTH_SCHEME, SYSTEM_PAGE_NAMES,
)
from apex_export_to_md.models import ApexPage
from apex_export_to_md.parser.yaml_helpers import strip_apex_id

logger = logging.getLogger(__name__)


class PageFilter:
    """Filtruje strony APEX zgodnie z konfiguracją."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._mode, self._param = self._parse_filter_spec(config.page_filter)

    @staticmethod
    def _parse_filter_spec(spec: str) -> tuple[str, str]:
        """Parsuj specyfikację filtra, np. 'prefix:DAW_' → ('prefix', 'DAW_')."""
        if ":" in spec:
            mode, param = spec.split(":", 1)
            return mode.strip(), param.strip()
        return spec.strip(), ""

    def filter_pages(self, pages: list[ApexPage]) -> list[ApexPage]:
        """Filtruj listę stron zgodnie z konfiguracją.

        Returns:
            Lista stron spełniających kryteria filtra
        """
        extra_ids = set(self._config.extra_pages)

        if self._mode == "all":
            return list(pages)

        elif self._mode == "prefix":
            prefix = self._param
            return [
                p for p in pages
                if p.name.startswith(prefix) or p.id in extra_ids
            ]

        elif self._mode == "ids":
            allowed_ids = set()
            for part in self._param.split(","):
                part = part.strip()
                if part.isdigit():
                    allowed_ids.add(int(part))
            allowed_ids.update(extra_ids)
            return [p for p in pages if p.id in allowed_ids]

        else:
            # Tryb auto — heurystyki
            result: list[ApexPage] = []
            for page in pages:
                if page.id in extra_ids:
                    result.append(page)
                    continue
                if self._is_standard_page(page):
                    logger.debug("Pomijam stronę standardową: %s (ID=%d)", page.name, page.id)
                    continue
                result.append(page)
            return result

    def _is_standard_page(self, page: ApexPage) -> bool:
        """Sprawdź, czy strona jest standardową stroną APEX (do pominięcia).

        Heurystyki:
        1. page_group w STANDARD_PAGE_GROUPS
        2. authorization-scheme = STANDARD_AUTH_SCHEME
        3. name w SYSTEM_PAGE_NAMES
        """
        # Heurystyka 1: grupa stron
        if page.page_group and page.page_group in STANDARD_PAGE_GROUPS:
            return True

        # Heurystyka 2: schemat autoryzacji
        auth_scheme = page.security.get("authorization-scheme", "")
        if auth_scheme:
            clean_auth = strip_apex_id(str(auth_scheme)) or ""
            if clean_auth == STANDARD_AUTH_SCHEME:
                return True

        # Heurystyka 3: znane nazwy systemowe
        if page.name in SYSTEM_PAGE_NAMES:
            return True

        return False
```

- [ ] **Step 3: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_page_filter.py -v
```

Expected: 8 PASSED

- [ ] **Step 4: Commit**

```bash
git add apex_export_to_md/filters/ tests/test_page_filter.py
git commit -m "feat: filtr stron APEX (heurystyki auto + prefix/ids/all)"
```

---

### Task 8: Base renderer + Human renderer

**Files:**
- Create: `apex_export_to_md/renderers/__init__.py`
- Create: `apex_export_to_md/renderers/base_renderer.py`
- Create: `apex_export_to_md/renderers/human_renderer.py`
- Create: `tests/test_human_renderer.py`

- [ ] **Step 1: Utwórz `apex_export_to_md/renderers/__init__.py`**

```python
"""Renderery — konwersja modelu APEX na format tekstowy."""
```

- [ ] **Step 2: Utwórz klasę bazową**

Plik: `apex_export_to_md/renderers/base_renderer.py`

```python
"""Abstrakcyjna klasa bazowa rendererów.

Definiuje interfejs wspólny dla wszystkich formatów wyjściowych.
Nowe renderery (np. JSON, HTML) powinny dziedziczyć po BaseRenderer.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from apex_export_to_md.models import ApexApp
from apex_export_to_md.config import AppConfig


class BaseRenderer(ABC):
    """Bazowy renderer — generuje tekst z modelu ApexApp."""

    def __init__(self, config: AppConfig):
        self._config = config

    @abstractmethod
    def render(self, app: ApexApp) -> str:
        """Generuj pełny tekst wyjściowy.

        Args:
            app: Model aplikacji APEX

        Returns:
            Tekst w docelowym formacie
        """
        ...

    def _should_include_code(self) -> bool:
        """Czy dołączyć pełny kod PL/SQL/JS."""
        return self._config.include_code == "full"

    def _should_summarize_code(self) -> bool:
        """Czy dołączyć skrócony kod (sygnatura + ...)."""
        return self._config.include_code == "summary"

    def _render_code_or_summary(self, code: str | None, lang: str = "sql") -> list[str]:
        """Renderuj kod w trybie full/summary/none.

        Returns:
            Lista linii z blokiem kodu, skrótem, lub pusta lista
        """
        if not code:
            return []
        if self._should_include_code():
            return [f"```{lang}", code, "```"]
        elif self._should_summarize_code():
            first_line = code.strip().split("\n")[0]
            return [f"> `{first_line}...`"]
        return []
```

- [ ] **Step 3: Napisz testy human renderera**

Plik: `tests/test_human_renderer.py`

```python
"""Testy human renderera (Markdown)."""
from apex_export_to_md.renderers.human_renderer import HumanRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, Button,
    Authorization, AppItem, BuildOption, AclRole,
)


def _make_app_with_page() -> ApexApp:
    """Utwórz minimalną aplikację z jedną stroną do testów."""
    col = Column(name="ID_PK", type="Hidden", primary_key=True,
                 source_column="ID_PK", data_type="NUMBER")
    col2 = Column(name="NUMER", type="Link", heading="Numer",
                  source_column="NUMER", link_target="6")
    region = Region(
        name="Lista", title="Lista audytów", type="Interactive Grid",
        source_table="B_AUDYT", editable=True,
        allowed_operations=["Add Row", "Update Row"],
        columns=[col, col2],
    )
    proc = Process(name="Zapisz", type="Execute Code", language="PL/SQL",
                   point="After Submit", code="BEGIN SAVE; END;",
                   when_button_pressed="SAVE")
    btn = Button(name="SAVE", label="Zapisz", action="Submit Page", is_hot=True)
    page = ApexPage(
        id=4, name="DAW_LISTA", title="Lista",
        regions=[region], processes=[proc], buttons=[btn],
        css_inline=".row { color: red; }",
    )
    return ApexApp(
        name="TEST_APP", id="100", alias="TEST",
        pages=[page],
        lovs=[LOV(name="LOV1", source_type="Table / View",
                  source_table="T1", return_column="ID", display_column="NAME")],
        authorizations=[Authorization(name="Admin", type="Is In Role",
                                       role_or_group="Administrator")],
        app_items=[AppItem(name="G_USER", scope="Global")],
        build_options=[BuildOption(name="Feature: X", status="Include")],
        acl_roles=[AclRole(name="Admin", static_id="ADMIN")],
    )


def test_render_zawiera_naglowek():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "# Aplikacja TEST_APP" in output
    assert "ID: 100" in output


def test_render_zawiera_strone():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "### Strona 4: DAW_LISTA" in output


def test_render_zawiera_region_z_kolumnami():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "Interactive Grid" in output
    assert "B_AUDYT" in output
    assert "ID_PK" in output
    assert "NUMER" in output


def test_render_zawiera_procesy():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "BEGIN SAVE; END;" in output
    assert "Zapisz" in output


def test_render_zawiera_css():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert ".row { color: red; }" in output


def test_render_zawiera_shared_components():
    renderer = HumanRenderer(AppConfig())
    output = renderer.render(_make_app_with_page())
    assert "LOV1" in output
    assert "Table / View" in output
    assert "Admin" in output


def test_render_bez_kodu():
    renderer = HumanRenderer(AppConfig(include_code="none"))
    output = renderer.render(_make_app_with_page())
    assert "BEGIN SAVE; END;" not in output


def test_render_bez_shared():
    renderer = HumanRenderer(AppConfig(include_shared_components=False))
    output = renderer.render(_make_app_with_page())
    assert "LOV1" not in output
```

- [ ] **Step 4: Zaimplementuj human renderer**

Plik: `apex_export_to_md/renderers/human_renderer.py`

```python
"""Human Renderer — generuje czytelny Markdown z modelu APEX.

Format wyjściowy: nagłówki, tabele, bloki kodu — czytelny dla człowieka.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)


class HumanRenderer(BaseRenderer):
    """Renderer Markdown czytelny dla człowieka."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny dokument Markdown."""
        lines: list[str] = []

        # Nagłówek aplikacji
        lines.append(f"# Aplikacja {app.name} (ID: {app.id}, alias: {app.alias})")
        lines.append("")

        # Strony
        if app.pages:
            lines.append("## Strony użytkownika")
            lines.append("")
            for page in app.pages:
                lines.extend(self._render_page(page))

        # Shared components
        if self._config.include_shared_components:
            sc_lines = self._render_shared_components(app)
            if sc_lines:
                lines.append("---")
                lines.append("")
                lines.extend(sc_lines)

        return "\n".join(lines)

    def _render_page(self, page: ApexPage) -> list[str]:
        """Renderuj pojedynczą stronę."""
        lines: list[str] = []
        lines.append(f"### Strona {page.id}: {page.name}")
        if page.title and page.title != page.name:
            lines.append(f"- **Tytuł:** {page.title}")
        lines.append(f"- **Tryb:** {page.page_mode}")
        if page.security:
            auth = page.security.get("authentication", "")
            if auth:
                lines.append(f"- **Uwierzytelnianie:** {auth}")
        lines.append("")

        # Regiony
        for region in page.regions:
            lines.extend(self._render_region(region))

        # Elementy formularza
        if page.items:
            lines.append("#### Elementy formularza")
            lines.append("")
            lines.append("| Nazwa | Typ | Etykieta | Kolumna | LOV |")
            lines.append("|-------|-----|----------|---------|-----|")
            for item in page.items:
                lines.append(
                    f"| {item.name} | {item.type} "
                    f"| {item.label or '—'} | {item.source_column or '—'} "
                    f"| {item.lov or '—'} |"
                )
            lines.append("")

        # Przyciski
        if page.buttons:
            lines.append("#### Przyciski")
            lines.append("")
            for btn in page.buttons:
                hot = " **(primary)**" if btn.is_hot else ""
                target = f" → strona {btn.target_page}" if btn.target_page else ""
                lines.append(f"- **{btn.name}** — {btn.label or '?'} [{btn.action or '?'}]{hot}{target}")
            lines.append("")

        # Procesy
        if page.processes:
            lines.append("#### Procesy")
            lines.append("")
            for proc in page.processes:
                btn_info = f", przycisk: {proc.when_button_pressed}" if proc.when_button_pressed else ""
                lang_info = f", język: {proc.language}" if proc.language else ""
                lines.append(f"**{proc.name}** ({proc.point}{lang_info}{btn_info})")
                lines.append("")
                if proc.code and self._should_include_code():
                    lang_hint = (proc.language or "sql").lower().replace("/", "")
                    lines.append(f"```{lang_hint}")
                    lines.append(proc.code)
                    lines.append("```")
                    lines.append("")
                elif proc.code and self._should_summarize_code():
                    first_line = proc.code.strip().split("\n")[0]
                    lines.append(f"> `{first_line}...`")
                    lines.append("")

        # Akcje dynamiczne
        if page.dynamic_actions:
            lines.append("#### Akcje dynamiczne")
            lines.append("")
            for da in page.dynamic_actions:
                trigger_info = f" na {da.selection_type}: {da.trigger_selector}" if da.trigger_selector else ""
                lines.append(f"- **{da.name}** — zdarzenie: {da.event}{trigger_info}")
                for step in da.actions:
                    lines.append(f"  - Krok: {step.type}")
                    if step.affected_elements:
                        lines.append(f"    - Wpływa na: {step.affected_elements}")
                    if step.code and self._should_include_code():
                        lines.append(f"    ```")
                        lines.append(f"    {step.code}")
                        lines.append(f"    ```")
            lines.append("")

        # Rozgałęzienia
        if page.branches:
            lines.append("#### Rozgałęzienia")
            lines.append("")
            for branch in page.branches:
                target = f"strona {branch.target_page}" if branch.target_page else branch.target_url or "?"
                cond = f" (warunek: {branch.condition})" if branch.condition else ""
                lines.append(f"- {branch.name or '?'} → {target}{cond}")
            lines.append("")

        # Walidacje
        if page.validations:
            lines.append("#### Walidacje")
            lines.append("")
            for val in page.validations:
                lines.append(f"- **{val.name}** — typ: {val.type}")
                if val.code and self._should_include_code():
                    lines.append(f"  ```plsql")
                    lines.append(f"  {val.code}")
                    lines.append(f"  ```")
            lines.append("")

        # CSS/JS
        if page.css_inline:
            lines.append("#### CSS strony")
            lines.append("")
            lines.append("```css")
            lines.append(page.css_inline)
            lines.append("```")
            lines.append("")

        if page.js_inline:
            lines.append("#### JavaScript strony")
            lines.append("")
            lines.append("```javascript")
            lines.append(page.js_inline)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _render_region(self, region: Region) -> list[str]:
        """Renderuj region z kolumnami."""
        lines: list[str] = []
        title_part = f' — "{region.title}"' if region.title else ""
        lines.append(f"#### Region: {region.name}{title_part}")

        # Typ i źródło
        type_info = region.type
        if region.editable:
            ops = ", ".join(region.allowed_operations) if region.allowed_operations else "?"
            type_info += f" (edytowalny: {ops})"

        lines.append(f"- **Typ:** {type_info}")
        if region.source_table:
            lines.append(f"- **Źródło:** tabela `{region.source_table}`")
        if region.source_sql:
            lines.append(f"- **Źródło SQL:**")
            if self._should_include_code():
                lines.append(f"```sql")
                lines.append(region.source_sql)
                lines.append(f"```")
        lines.append("")

        # Kolumny jako tabela
        if region.columns:
            lines.append("| Kolumna | Typ | Nagłówek | Źródło | PK | Link |")
            lines.append("|---------|-----|----------|--------|----|------|")
            for col in region.columns:
                pk = "tak" if col.primary_key else "—"
                link = f"→strona {col.link_target}" if col.link_target else "—"
                lines.append(
                    f"| {col.name} | {col.type} | {col.heading or '—'} "
                    f"| {col.source_column or '—'} | {pk} | {link} |"
                )
            lines.append("")

        return lines

    def _render_shared_components(self, app: ApexApp) -> list[str]:
        """Renderuj sekcję Shared Components."""
        lines: list[str] = []
        lines.append("## Shared Components")
        lines.append("")

        # LOV-y
        if app.lovs:
            lines.append("### Listy wartości (LOV)")
            lines.append("")
            for lov in app.lovs:
                lines.append(f"**{lov.name}** — typ: {lov.source_type}")
                if lov.source_table:
                    lines.append(f"- Tabela: `{lov.source_table}`")
                if lov.return_column:
                    lines.append(f"- Return: `{lov.return_column}`")
                if lov.display_column:
                    lines.append(f"- Display: `{lov.display_column}`")
                if lov.sql_query and self._should_include_code():
                    lines.append(f"```sql")
                    lines.append(lov.sql_query)
                    lines.append(f"```")
                if lov.entries:
                    vals = ", ".join(f"{e['display']}→{e['return']}" for e in lov.entries)
                    lines.append(f"- Wartości: {vals}")
                lines.append("")

        # Autoryzacje
        if app.authorizations:
            lines.append("### Schematy autoryzacji")
            lines.append("")
            for auth in app.authorizations:
                lines.append(f"**{auth.name}** — typ: {auth.type or '?'}")
                if auth.role_or_group:
                    lines.append(f"- Rola: {auth.role_or_group}")
                if auth.code and self._should_include_code():
                    lines.append(f"```plsql")
                    lines.append(auth.code)
                    lines.append(f"```")
                lines.append("")

        # Nawigacja
        if app.nav_lists:
            lines.append("### Listy nawigacyjne")
            lines.append("")
            for nav in app.nav_lists:
                lines.append(f"**{nav.name}**")
                for entry in nav.entries:
                    label = entry.get("label", "?")
                    target = entry.get("target_page", "?")
                    lines.append(f"- {label} → {target}")
                lines.append("")

        # App Items
        if app.app_items:
            lines.append("### Zmienne globalne")
            lines.append("")
            lines.append("| Nazwa | Zakres |")
            lines.append("|-------|--------|")
            for item in app.app_items:
                lines.append(f"| {item.name} | {item.scope or '?'} |")
            lines.append("")

        # Build Options
        if app.build_options:
            lines.append("### Opcje budowania")
            lines.append("")
            for bo in app.build_options:
                lines.append(f"- **{bo.name}** — {bo.status}")
            lines.append("")

        # Breadcrumbs
        if app.breadcrumbs:
            lines.append("### Breadcrumbs")
            lines.append("")
            for bc in app.breadcrumbs:
                entries_str = " → ".join(
                    f"{e.get('name', '?')} (strona {e.get('page_number', '?')})"
                    for e in bc.entries
                )
                lines.append(f"- **{bc.name}:** {entries_str}")
            lines.append("")

        # ACL Roles
        if app.acl_roles:
            lines.append("### Role ACL")
            lines.append("")
            for role in app.acl_roles:
                lines.append(f"- **{role.name}** (static_id: {role.static_id or '?'})")
            lines.append("")

        return lines
```

- [ ] **Step 5: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_human_renderer.py -v
```

Expected: 8 PASSED

- [ ] **Step 6: Commit**

```bash
git add apex_export_to_md/renderers/ tests/test_human_renderer.py
git commit -m "feat: human renderer (Markdown z tabelami i blokami kodu)"
```

---

### Task 9: LLM renderer

**Files:**
- Create: `apex_export_to_md/renderers/llm_renderer.py`
- Create: `tests/test_llm_renderer.py`

- [ ] **Step 1: Napisz testy**

Plik: `tests/test_llm_renderer.py`

```python
"""Testy LLM renderera (format skondensowany)."""
from apex_export_to_md.renderers.llm_renderer import LLMRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, LOV, Process, Button,
    Authorization, AppItem, BuildOption, AclRole, DynamicAction,
    DynamicActionStep,
)


def _make_app() -> ApexApp:
    col = Column(name="ID_PK", type="Hidden", primary_key=True)
    col2 = Column(name="NUMER", type="Link", heading="Numer", link_target="6")
    region = Region(
        name="Lista", title="Audyty", type="Interactive Grid",
        source_table="B_AUDYT", editable=True,
        allowed_operations=["Add Row"], columns=[col, col2],
    )
    proc = Process(name="Zapisz", type="Execute Code", language="PL/SQL",
                   point="After Submit", code="BEGIN SAVE; END;",
                   when_button_pressed="SAVE")
    da = DynamicAction(
        name="Zmiana", event="Change", selection_type="Item",
        trigger_selector="P4_STATUS",
        actions=[DynamicActionStep(type="Execute PL/SQL Code", code="NULL;")],
    )
    page = ApexPage(
        id=4, name="DAW_LISTA", regions=[region],
        processes=[proc], dynamic_actions=[da],
        buttons=[Button(name="SAVE", label="Zapisz", action="Submit Page", is_hot=True)],
    )
    return ApexApp(
        name="TEST", id="100", alias="T",
        pages=[page],
        lovs=[LOV(name="L1", source_type="Table / View", source_table="T1",
                  return_column="ID", display_column="NAME")],
        authorizations=[Authorization(name="Admin", type="Is In Role",
                                       role_or_group="Adm")],
    )


def test_render_format_liniowy():
    """Sprawdza, że wyjście używa formatu liniowego z prefiksami."""
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert output.startswith("APP:100|T|TEST")
    assert "===PAGE:4|DAW_LISTA" in output


def test_render_region_kolumny():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "RGN:Lista|" in output
    assert "COL:ID_PK|Hidden|pk:true" in output
    assert "COL:NUMER|Link|heading:Numer|link:page6" in output


def test_render_process_z_kodem():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "PROC:Zapisz|" in output
    assert "BEGIN SAVE; END;" in output


def test_render_da():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "DA:Zmiana|event:Change" in output
    assert "DA_STEP:Execute PL/SQL Code" in output


def test_render_lov():
    renderer = LLMRenderer(AppConfig())
    output = renderer.render(_make_app())
    assert "===LOV:L1|type:Table|" in output


def test_render_bez_kodu():
    renderer = LLMRenderer(AppConfig(include_code="none"))
    output = renderer.render(_make_app())
    assert "BEGIN SAVE; END;" not in output
```

- [ ] **Step 2: Zaimplementuj LLM renderer**

Plik: `apex_export_to_md/renderers/llm_renderer.py`

```python
"""LLM Renderer — generuje skondensowany format liniowy zoptymalizowany pod tokenizer.

Minimalizuje zużycie tokenów przy zachowaniu pełnej informacji.
Format: prefiksy typu (APP, PAGE, RGN, COL, ITEM, BTN, PROC, DA, ...) z wartościami
oddzielonymi znakiem |.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)


class LLMRenderer(BaseRenderer):
    """Renderer zoptymalizowany dla LLM — format liniowy."""

    def render(self, app: ApexApp) -> str:
        """Generuj skondensowany tekst."""
        lines: list[str] = []

        # Nagłówek aplikacji
        lines.append(f"APP:{app.id}|{app.alias}|{app.name}")

        # Strony
        for page in app.pages:
            lines.extend(self._render_page(page))

        # Shared components
        if self._config.include_shared_components:
            lines.extend(self._render_shared(app))

        return "\n".join(lines)

    def _render_page(self, page: ApexPage) -> list[str]:
        """Renderuj stronę w formacie liniowym."""
        lines: list[str] = []

        # Nagłówek strony
        auth = "auth:required" if page.security.get("authentication") else ""
        parts = [f"===PAGE:{page.id}", page.name, page.page_mode]
        if auth:
            parts.append(auth)
        lines.append("|".join(parts))

        # CSS/JS
        if page.css_inline:
            lines.append("CSS:inline")
            lines.append(page.css_inline)
            lines.append("---")
        if page.js_inline:
            lines.append("JS:inline")
            lines.append(page.js_inline)
            lines.append("---")

        # Regiony
        for region in page.regions:
            lines.extend(self._render_region(region))

        # Elementy formularza
        for item in page.items:
            parts = [f"ITEM:{item.name}", item.type]
            if item.label:
                parts.append(f"label:{item.label}")
            if item.source_column:
                parts.append(f"col:{item.source_column}")
            if item.lov:
                parts.append(f"lov:{item.lov}")
            lines.append("|".join(parts))

        # Przyciski
        for btn in page.buttons:
            parts = [f"BTN:{btn.name}"]
            if btn.label:
                parts.append(f"label:{btn.label}")
            if btn.action:
                parts.append(f"action:{btn.action}")
            if btn.is_hot:
                parts.append("hot:true")
            if btn.target_page:
                parts.append(f"target:page{btn.target_page}")
            lines.append("|".join(parts))

        # Procesy
        for proc in page.processes:
            parts = [f"PROC:{proc.name}", proc.type]
            if proc.language:
                parts.append(f"lang:{proc.language}")
            parts.append(f"point:{proc.point}")
            if proc.when_button_pressed:
                parts.append(f"btn:{proc.when_button_pressed}")
            lines.append("|".join(parts))
            if proc.code:
                lang = (proc.language or "sql").lower().replace("/", "")
                lines.extend(self._render_code_or_summary(proc.code, lang))

        # Akcje dynamiczne
        for da in page.dynamic_actions:
            parts = [f"DA:{da.name}", f"event:{da.event}"]
            if da.selection_type:
                parts.append(f"sel:{da.selection_type}")
            if da.trigger_selector:
                parts.append(f"trigger:{da.trigger_selector}")
            if da.event_scope:
                parts.append(f"scope:{da.event_scope}")
            lines.append("|".join(parts))
            for step in da.actions:
                step_parts = [f"DA_STEP:{step.type}"]
                if step.affected_elements:
                    step_parts.append(f"affects:{step.affected_elements}")
                lines.append("|".join(step_parts))
                if step.code:
                    lines.extend(self._render_code_or_summary(step.code, "plsql"))

        # Rozgałęzienia
        for branch in page.branches:
            target = f"page:{branch.target_page}" if branch.target_page else branch.target_url or "?"
            parts = [f"BRANCH:{branch.type}->{target}"]
            if branch.condition:
                parts.append(f"cond:{branch.condition}")
            lines.append("|".join(parts))

        # Walidacje
        for val in page.validations:
            parts = [f"VAL:{val.name}", f"type:{val.type}"]
            lines.append("|".join(parts))
            if val.code:
                lines.extend(self._render_code_or_summary(val.code, "plsql"))

        return lines

    def _render_region(self, region: Region) -> list[str]:
        """Renderuj region i jego kolumny."""
        lines: list[str] = []
        parts = [f"RGN:{region.name}"]
        if region.title:
            parts.append(f"title:{region.title}")
        parts.append(region.type)
        if region.source_table:
            parts.append(f"src:{region.source_table}")
        if region.source_sql and self._should_include_code():
            parts.append("src:SQL")
        if region.editable:
            parts.append("edit:true")
            if region.allowed_operations:
                ops = ",".join(o.split(" ")[0] for o in region.allowed_operations)
                parts.append(f"ops:{ops}")
        lines.append("|".join(parts))

        # SQL źródłowy
        if region.source_sql and self._should_include_code():
            lines.append("```sql")
            lines.append(region.source_sql)
            lines.append("```")

        # Kolumny
        for col in region.columns:
            col_parts = [f"COL:{col.name}", col.type]
            if col.heading:
                col_parts.append(f"heading:{col.heading}")
            if col.primary_key:
                col_parts.append("pk:true")
            if col.link_target:
                col_parts.append(f"link:page{col.link_target}")
            if col.lov:
                col_parts.append(f"lov:{col.lov}")
            lines.append("|".join(col_parts))

        return lines

    def _render_shared(self, app: ApexApp) -> list[str]:
        """Renderuj shared components."""
        lines: list[str] = []

        for lov in app.lovs:
            parts = [f"===LOV:{lov.name}"]
            # Skrócony typ
            type_short = {"Table / View": "Table", "SQL Query": "SQL",
                          "Static Values": "Static"}.get(lov.source_type, lov.source_type)
            parts.append(f"type:{type_short}")
            if lov.source_table:
                parts.append(f"tbl:{lov.source_table}")
            if lov.return_column:
                parts.append(f"ret:{lov.return_column}")
            if lov.display_column:
                parts.append(f"disp:{lov.display_column}")
            lines.append("|".join(parts))
            if lov.sql_query and self._should_include_code():
                lines.append("```sql")
                lines.append(lov.sql_query)
                lines.append("```")
            if lov.entries:
                vals = "|".join(f"{e['display']}:{e['return']}" for e in lov.entries)
                lines.append(f"ENTRIES:{vals}")

        for auth in app.authorizations:
            parts = [f"===AUTH:{auth.name}"]
            if auth.type:
                parts.append(f"type:{auth.type}")
            if auth.role_or_group:
                parts.append(f"role:{auth.role_or_group}")
            lines.append("|".join(parts))
            if auth.code and self._should_include_code():
                lines.append("```plsql")
                lines.append(auth.code)
                lines.append("```")

        for nav in app.nav_lists:
            entries_str = "|".join(
                f"{e.get('label', '?')}->page:{e.get('target_page', '?')}"
                for e in nav.entries
            )
            lines.append(f"===NAV:{nav.name}|{entries_str}")

        for item in app.app_items:
            lines.append(f"===APP_ITEM:{item.name}|scope:{item.scope or '?'}")

        for bo in app.build_options:
            lines.append(f"===BUILD_OPT:{bo.name}|status:{bo.status}")

        for bc in app.breadcrumbs:
            entries_str = "->".join(
                f"{e.get('name', '?')}:page{e.get('page_number', '?')}"
                for e in bc.entries
            )
            lines.append(f"===BREADCRUMB:{bc.name}|{entries_str}")

        for role in app.acl_roles:
            lines.append(f"===ACL:{role.name}|static_id:{role.static_id or '?'}")

        return lines
```

- [ ] **Step 3: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_llm_renderer.py -v
```

Expected: 6 PASSED

- [ ] **Step 4: Commit**

```bash
git add apex_export_to_md/renderers/llm_renderer.py tests/test_llm_renderer.py
git commit -m "feat: LLM renderer (skondensowany format liniowy)"
```

---

### Task 10: CLI — punkt wejścia

**Files:**
- Create: `apex_export_to_md/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Napisz testy CLI**

Plik: `tests/test_cli.py`

```python
"""Testy CLI (parsowanie argumentów)."""
from apex_export_to_md.cli import parse_args


def test_parse_args_minimalne():
    """Minimalne wywołanie — tylko ścieżka."""
    args = parse_args(["/path/to/export"])
    assert args.input_dir == "/path/to/export"
    assert args.format == "both"
    assert args.include_code == "full"
    assert args.page_filter == "auto"


def test_parse_args_pelne():
    """Pełne wywołanie z wszystkimi opcjami."""
    args = parse_args([
        "/path",
        "--output-dir", "/out",
        "--output-prefix", "my_export",
        "--format", "llm",
        "--include-code", "none",
        "--page-filter", "prefix:DAW_",
        "--extra-pages", "1,9999",
        "--include-internal-ids",
        "--include-layout",
        "--no-shared-components",
        "--verbose",
    ])
    assert args.output_dir == "/out"
    assert args.output_prefix == "my_export"
    assert args.format == "llm"
    assert args.include_code == "none"
    assert args.page_filter == "prefix:DAW_"
    assert args.extra_pages == "1,9999"
    assert args.include_internal_ids is True
    assert args.include_layout is True
    assert args.no_shared_components is True
    assert args.verbose is True
```

- [ ] **Step 2: Zaimplementuj CLI**

Plik: `apex_export_to_md/cli.py`

```python
"""Punkt wejścia CLI — parsowanie argumentów i orkiestracja pipeline'u.

Użycie:
    python -m apex_export_to_md <ścieżka_do_exportu> [opcje]
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp
from apex_export_to_md.parser.page_parser import parse_all_pages
from apex_export_to_md.parser.shared_parser import (
    load_yaml_file, parse_app_definition, parse_shared_components,
)
from apex_export_to_md.filters.page_filter import PageFilter
from apex_export_to_md.renderers.human_renderer import HumanRenderer
from apex_export_to_md.renderers.llm_renderer import LLMRenderer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parsuj argumenty wiersza poleceń."""
    parser = argparse.ArgumentParser(
        prog="apex_export_to_md",
        description="Konwertuje eksport Oracle APEX (readable YAML) na Markdown.",
    )
    parser.add_argument(
        "input_dir",
        help="Ścieżka do katalogu eksportu APEX (zawierającego pages/ i shared_components/)",
    )
    parser.add_argument(
        "--output-dir", default=".",
        help="Katalog wyjściowy (domyślnie: bieżący)",
    )
    parser.add_argument(
        "--output-prefix", default="apex_export",
        help="Prefiks nazw plików wyjściowych (domyślnie: apex_export)",
    )
    parser.add_argument(
        "--format", choices=["both", "human", "llm"], default="both",
        help="Które pliki generować (domyślnie: both)",
    )
    parser.add_argument(
        "--include-code", choices=["full", "summary", "none"], default="full",
        help="Jak traktować bloki PL/SQL/JS (domyślnie: full)",
    )
    parser.add_argument(
        "--page-filter", default="auto",
        help="Filtr stron: auto, all, prefix:<X>, ids:<1,2,3> (domyślnie: auto)",
    )
    parser.add_argument(
        "--extra-pages", default="",
        help="Dodatkowe strony do dołączenia (ID rozdzielone przecinkami)",
    )
    parser.add_argument(
        "--include-internal-ids", action="store_true",
        help="Zachowaj wewnętrzne ID APEX",
    )
    parser.add_argument(
        "--include-layout", action="store_true",
        help="Zachowaj szczegóły layoutu",
    )
    parser.add_argument(
        "--no-shared-components", action="store_true",
        help="Pomiń shared components",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Szczegółowe logi",
    )
    return parser.parse_args(argv)


def args_to_config(args: argparse.Namespace) -> AppConfig:
    """Konwertuj argumenty CLI na obiekt konfiguracji."""
    extra_pages: list[int] = []
    if args.extra_pages:
        for part in args.extra_pages.split(","):
            part = part.strip()
            if part.isdigit():
                extra_pages.append(int(part))

    return AppConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
        output_format=args.format,
        include_code=args.include_code,
        page_filter=args.page_filter,
        extra_pages=extra_pages,
        include_internal_ids=args.include_internal_ids,
        include_layout=args.include_layout,
        include_shared_components=not args.no_shared_components,
        verbose=args.verbose,
    )


def find_app_root(input_dir: Path) -> Path:
    """Znajdź katalog główny aplikacji APEX.

    Szuka katalogu zawierającego pages/ i (opcjonalnie) shared_components/.
    Obsługuje zarówno bezpośrednie podanie katalogu application/,
    jak i katalogu nadrzędnego (program/readable/).
    """
    # Bezpośrednio — katalog zawiera pages/
    if (input_dir / "pages").is_dir():
        return input_dir

    # Szukaj w podkatalogach (np. readable/application/)
    for candidate in input_dir.rglob("pages"):
        if candidate.is_dir():
            return candidate.parent

    return input_dir


def run_pipeline(config: AppConfig) -> None:
    """Uruchom pełny pipeline: parse → filter → render → zapis."""
    input_path = Path(config.input_dir)
    if not input_path.exists():
        logging.error("Katalog nie istnieje: %s", input_path)
        sys.exit(1)

    app_root = find_app_root(input_path)
    pages_dir = app_root / "pages"
    shared_dir = app_root / "shared_components"

    logging.info("Katalog aplikacji: %s", app_root)

    # 1. Parsuj plik główny aplikacji (f*.yaml)
    app_name, app_id, app_alias = "", "", ""
    for f_yaml in app_root.glob("f*.yaml"):
        data = load_yaml_file(f_yaml)
        if data:
            app_name, app_id, app_alias = parse_app_definition(data)
            break

    # 2. Parsuj strony
    all_pages = parse_all_pages(pages_dir)
    logging.info("Sparsowano %d stron", len(all_pages))

    # 3. Filtruj strony
    page_filter = PageFilter(config)
    filtered_pages = page_filter.filter_pages(all_pages)
    logging.info("Po filtracji: %d stron", len(filtered_pages))

    # 4. Parsuj shared components
    shared = {}
    if config.include_shared_components:
        shared = parse_shared_components(shared_dir)

    # 5. Zbuduj model aplikacji
    app = ApexApp(
        name=app_name or "APEX App",
        id=app_id or "?",
        alias=app_alias or "?",
        pages=filtered_pages,
        **shared,
    )

    # 6. Renderuj i zapisz
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if config.output_format in ("both", "human"):
        renderer = HumanRenderer(config)
        content = renderer.render(app)
        out_path = output_dir / f"{config.output_prefix}_human.md"
        out_path.write_text(content, encoding="utf-8")
        logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    if config.output_format in ("both", "llm"):
        renderer = LLMRenderer(config)
        content = renderer.render(app)
        out_path = output_dir / f"{config.output_prefix}_llm.md"
        out_path.write_text(content, encoding="utf-8")
        logging.info("Zapisano: %s (%d znaków)", out_path, len(content))


def main():
    """Główna funkcja CLI."""
    args = parse_args()
    config = args_to_config(args)

    # Konfiguracja logowania
    log_level = logging.DEBUG if config.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    run_pipeline(config)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Uruchom testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_cli.py -v
```

Expected: 2 PASSED

- [ ] **Step 4: Commit**

```bash
git add apex_export_to_md/cli.py apex_export_to_md/__main__.py tests/test_cli.py
git commit -m "feat: CLI i orkiestracja pipeline'u"
```

---

### Task 11: Test integracyjny z prawdziwymi danymi

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Napisz test integracyjny**

Plik: `tests/test_integration.py`

```python
"""Test integracyjny — uruchomienie pełnego pipeline'u na prawdziwych danych projektu."""
import os
from pathlib import Path
import pytest

from apex_export_to_md.config import AppConfig
from apex_export_to_md.cli import run_pipeline


# Ścieżka do prawdziwych danych — pomiń test jeśli brak
REAL_DATA_DIR = Path(os.environ.get(
    "APEX_EXPORT_DIR",
    "c:/_projekty/SKW_TO_APEX/program/readable/application",
))


@pytest.mark.skipif(
    not REAL_DATA_DIR.exists(),
    reason=f"Brak danych testowych: {REAL_DATA_DIR}",
)
class TestIntegration:

    def test_pipeline_both_formats(self, tmp_path):
        """Pipeline generuje oba pliki bez błędów."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_prefix="test_export",
            output_format="both",
        )
        run_pipeline(config)

        human_file = tmp_path / "test_export_human.md"
        llm_file = tmp_path / "test_export_llm.md"

        assert human_file.exists()
        assert llm_file.exists()

        human_content = human_file.read_text(encoding="utf-8")
        llm_content = llm_file.read_text(encoding="utf-8")

        # Minimalny rozmiar — obie wersje powinny mieć treść
        assert len(human_content) > 500
        assert len(llm_content) > 200

        # LLM powinien być mniejszy niż human
        assert len(llm_content) < len(human_content)

    def test_pipeline_filtruje_strony_admin(self, tmp_path):
        """Pipeline w trybie auto pomija strony administracyjne."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="human",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_human.md").read_text(encoding="utf-8")

        # Strony DAW_* powinny być obecne
        assert "DAW_LISTA_AUDYTOW" in content or "DAW_ANKIETA" in content

        # Strony administracyjne NIE powinny być obecne
        assert "Activity Dashboard" not in content
        assert "Configuration Options" not in content
        assert "Manage User Access" not in content

    def test_pipeline_zawiera_shared_components(self, tmp_path):
        """Pipeline dołącza LOV-y i autoryzacje."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="human",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_human.md").read_text(encoding="utf-8")
        assert "LOV" in content or "Lista wartości" in content
        assert "autoryzacj" in content.lower() or "AUTH" in content

    def test_pipeline_tryb_all(self, tmp_path):
        """Pipeline w trybie all zawiera wszystkie strony."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="llm",
            page_filter="all",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_llm.md").read_text(encoding="utf-8")
        assert "Administration" in content or "Global Page" in content
```

- [ ] **Step 2: Uruchom test integracyjny**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/test_integration.py -v
```

Expected: 4 PASSED

- [ ] **Step 3: Uruchom ręcznie na prawdziwych danych i sprawdź wyjście**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m apex_export_to_md program/readable/application --output-dir . --verbose
```

Expected: Dwa pliki `apex_export_human.md` i `apex_export_llm.md` w bieżącym katalogu.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: testy integracyjne z prawdziwymi danymi APEX"
```

---

### Task 12: Uruchom pełny zestaw testów i finalizacja

- [ ] **Step 1: Uruchom wszystkie testy**

```bash
cd c:/_projekty/SKW_TO_APEX && python -m pytest tests/ -v --tb=short
```

Expected: Wszystkie testy PASSED

- [ ] **Step 2: Sprawdź wygenerowane pliki**

Zweryfikuj ręcznie, że:
- `apex_export_human.md` zawiera czytelne tabele, nagłówki, bloki kodu
- `apex_export_llm.md` zawiera skondensowany format liniowy
- Strony DAW_* są obecne, strony administracyjne pominięte
- Shared components (LOV, autoryzacje, breadcrumbs) są dołączone

- [ ] **Step 3: Commit finalizacyjny**

```bash
git add -A
git commit -m "feat: APEX Export to Markdown Converter — kompletna implementacja"
```
