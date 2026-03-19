# APEX Export → Markdown Converter — Specyfikacja

## Cel

Program w Pythonie konwertujący strukturę katalogów eksportu Oracle APEX (format "readable") na dwa pliki Markdown:
1. **Human-readable** — czytelny dla człowieka, z tabelami, nagłówkami i blokami kodu
2. **LLM-optimized** — skondensowany format liniowy zoptymalizowany pod tokenizer LLM

Plik wynikowy ma zasilić model LLM kontekstem do dalszej pracy nad projektem APEX.

## Architektura

Pipeline z separacją warstw:

```
YAML files → Parser → [ApexApp model] → Filter → [filtered model] → Renderer → .md files
```

### Struktura plików

```
apex_export_to_md/
├── apex_export_to_md.py      # punkt wejścia CLI (argparse)
├── parser/
│   ├── __init__.py
│   ├── page_parser.py        # parsuje pliki pages/*.yaml
│   └── shared_parser.py      # parsuje shared_components/
├── models/
│   ├── __init__.py
│   └── apex_models.py        # dataclasses: ApexApp, ApexPage, Region, Column...
├── filters/
│   ├── __init__.py
│   └── page_filter.py        # heurystyki: które strony są "użytkownika"
├── renderers/
│   ├── __init__.py
│   ├── human_renderer.py     # Markdown z tabelami, nagłówkami, blokami kodu
│   └── llm_renderer.py       # skondensowany format tekstowy
└── config.py                 # przełączniki i stałe
```

## Modele danych (`models/apex_models.py`)

Wszystkie modele jako `@dataclass`:

```python
@dataclass
class ApexApp:
    name: str
    id: str
    alias: str
    pages: list[ApexPage]
    lovs: list[LOV]
    authorizations: list[Authorization]
    nav_lists: list[NavList]
    app_items: list[AppItem]
    build_options: list[BuildOption]
    breadcrumbs: list[Breadcrumb]
    acl_roles: list[AclRole]

@dataclass
class ApexPage:
    id: int
    name: str
    alias: str
    title: str
    page_group: str | None
    page_mode: str                  # Normal / Modal Dialog
    security: dict
    build_options: list[str]
    regions: list[Region]
    items: list[PageItem]
    buttons: list[Button]
    processes: list[Process]
    dynamic_actions: list[DynamicAction]
    branches: list[Branch]
    validations: list[Validation]
    css_inline: str | None          # bloki CSS na poziomie strony
    js_inline: str | None           # bloki JavaScript na poziomie strony

@dataclass
class Region:
    name: str
    title: str | None               # tytuł widoczny dla użytkownika (np. "Filtry wyszukiwania")
    type: str                       # Interactive Grid, Form, Static Content, Chart...
    source_table: str | None
    source_sql: str | None
    parent_region: str | None
    columns: list[Column]
    editable: bool                  # czy IG pozwala na edycję (attributes.edit.enabled)
    allowed_operations: list[str]   # np. ["Add Row", "Update Row", "Delete Row"]

@dataclass
class Column:
    name: str
    type: str                       # Link, Text, Hidden, Select...
    heading: str | None
    source_column: str | None
    data_type: str | None
    link_target: str | None
    lov: str | None
    primary_key: bool               # source.primary-key

@dataclass
class PageItem:
    name: str
    type: str                       # Text Field, Select List, Hidden...
    label: str | None
    source_column: str | None
    lov: str | None
    default_value: str | None

@dataclass
class Process:
    name: str
    type: str                       # Execute Code, Invoke API...
    language: str | None            # PL/SQL, JavaScript...
    point: str                      # Processing, After Submit...
    code: str | None
    condition: str | None
    when_button_pressed: str | None # powiązanie z przyciskiem

@dataclass
class DynamicAction:
    name: str
    event: str                      # Change, Click, Page Load...
    selection_type: str | None      # jQuery Selector, Region, Item, Button...
    trigger_selector: str | None    # jQuery selector lub nazwa regionu/elementu
    event_scope: str | None         # Dynamic, Static
    static_container: str | None    # jQuery selector kontenera dla delegacji zdarzeń
    actions: list[DynamicActionStep]

@dataclass
class DynamicActionStep:
    type: str                       # Execute PL/SQL Code, Execute JavaScript Code, Set Value...
    code: str | None                # treść PL/SQL lub JS
    affected_elements: str | None   # selektor docelowy
    fire_on_initialization: bool

@dataclass
class Button:
    name: str
    label: str | None
    action: str | None              # Submit Page, Redirect, Defined by Dynamic Action
    target_page: int | None
    is_hot: bool                    # appearance.hot — przycisk główny (primary)

@dataclass
class Branch:
    name: str | None                # np. "Go To Page 10044"
    type: str                       # Page or URL (Redirect)
    target_page: int | None
    target_url: str | None
    point: str                      # After Processing
    condition: str | None

@dataclass
class Validation:
    name: str
    type: str                       # PL/SQL Function Body, Item is NOT NULL...
    code: str | None
    condition: str | None

@dataclass
class LOV:
    name: str
    source_type: str                # Table / View, SQL Query, Static Values
    source_table: str | None        # dla Table / View
    sql_query: str | None           # dla SQL Query
    entries: list[dict] | None      # dla Static Values [{display, return}, ...]
    return_column: str | None
    display_column: str | None

@dataclass
class Authorization:
    name: str
    type: str | None                # Is In Role or Group, PL/SQL Function Returning Boolean...
    code: str | None                # treść PL/SQL (jeśli dotyczy)
    role_or_group: str | None       # nazwa roli (jeśli dotyczy)

@dataclass
class NavList:
    name: str
    entries: list[dict]

@dataclass
class AppItem:
    name: str
    scope: str | None

@dataclass
class BuildOption:
    name: str
    status: str                     # Include, Exclude

@dataclass
class Breadcrumb:
    name: str
    entries: list[dict]             # [{name, page_number, target_page}, ...]

@dataclass
class AclRole:
    name: str
    static_id: str | None
```

## Mapowanie YAML → Model

Klucze YAML są zagnieżdżone — poniżej konwencje mapowania na płaskie pola dataclass:

### Strona (ApexPage)
| Pole modelu | Klucz YAML |
|---|---|
| `id` | `id` (top-level) |
| `name` | `identification.name` |
| `alias` | `identification.alias` |
| `title` | `identification.title` |
| `page_group` | `identification.page-group` (tekst przed `#`) |
| `page_mode` | `appearance.page-mode` |
| `security` | `security` (cały blok jako dict) |
| `build_options` | zbierz wszystkie `build-option` z dowolnego poziomu zagnieżdżenia |
| `css_inline` | `css.inline` |
| `js_inline` | `javascript.execute-when-page-loads` lub `javascript.inline` |

### Region
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `title` | `identification.title` |
| `type` | `identification.type` |
| `source_table` | `source.table-name` |
| `source_sql` | `source.sql-query` |
| `parent_region` | `layout.parent-region` |
| `editable` | `attributes.edit.enabled` (domyślnie `false`) |
| `allowed_operations` | `attributes.edit.allowed-operations` (lista) |

### Kolumna (Column)
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.column-name` |
| `type` | `identification.type` |
| `heading` | `heading.heading` |
| `source_column` | `source.database-column` |
| `data_type` | `source.data-type` |
| `primary_key` | `source.primary-key` |
| `link_target` | `link.target.page` |
| `lov` | `list-of-values.list-of-values` |

### Button
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.button-name` |
| `label` | `label.label` |
| `action` | `behavior.action` |
| `target_page` | `behavior.target` (jeśli redirect) |
| `is_hot` | `appearance.hot` |

### Process
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `type` | `identification.type` |
| `language` | `source.language` |
| `code` | `source.pl/sql-code` lub `source.javascript-code` |
| `point` | `execution.point` |
| `condition` | `server-side-condition` (cały blok → string) |
| `when_button_pressed` | `server-side-condition.when-button-pressed` |

> **Uwaga:** Procesy typu "Invoke API" nie mają `source.pl/sql-code` — ich konfiguracja jest w `settings` (package, procedure-or-function). Parser powinien dla tego typu złożyć `code` z `settings.package` + `settings.procedure-or-function` jako tekst opisowy, np. `"INVOKE: package.procedure"`.

### DynamicAction
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `event` | `when.event` |
| `selection_type` | `when.selection-type` |
| `trigger_selector` | `when.jquery-selector` lub `when.region` lub `when.item` |
| `event_scope` | `execution.event-scope` |
| `static_container` | `execution.static-container-(jquery-selector)` |

### DynamicActionStep (wewnątrz `actions:` listy DA)
| Pole modelu | Klucz YAML |
|---|---|
| `type` | `identification.action` |
| `code` | `settings.pl/sql-code` lub `settings.javascript-code` |
| `affected_elements` | `affected-elements.selection-type` + `affected-elements.jquery-selector` |
| `fire_on_initialization` | `execution.fire-on-initialization` |

### Branch
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `type` | `behavior.type` |
| `target_page` | `behavior.target.page` |
| `target_url` | `behavior.target.url` |
| `point` | `execution.point` |
| `condition` | `server-side-condition` |

### LOV
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `source_type` | `source.type` |
| `source_table` | `source.table-name` (gdy type = Table / View) |
| `sql_query` | `source.sql-query` (gdy type = SQL Query) |
| `entries` | `entries` (lista, gdy type = Static Values) |
| `return_column` | `column-mapping.return` |
| `display_column` | `column-mapping.display` |

### Authorization
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `type` | `authorization-scheme.type` |
| `code` | `settings.pl/sql-function-body` |
| `role_or_group` | `settings.name(s)` (uwaga: nawiasy w nazwie klucza) |

### Validation
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `type` | `validation.type` (uwaga: nie `identification.type`) |
| `code` | `validation.pl/sql-function-body` |
| `condition` | `server-side-condition` (blok → string) |

### PageItem
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `type` | `identification.type` |
| `label` | `label.label` |
| `source_column` | `source.database-column` (gdy `source.type` = Database Column; inaczej `None`) |
| `lov` | `list-of-values.list-of-values` |
| `default_value` | `default.static-value` |

### NavList
| Pole modelu | Klucz YAML |
|---|---|
| `name` | `identification.name` |
| `entries[].text` | `entries[].entry.label` |
| `entries[].target_page` | `entries[].entry.target.page` |
| `entries[].parent` | `entries[].entry.parent-entry` |

## Filtrowanie (`filters/page_filter.py`)

### Heurystyki rozpoznawania stron standardowych APEX

Strona jest standardowa (do pominięcia) gdy spełnia **co najmniej jedno**:
- `page_group ∈ STANDARD_PAGE_GROUPS` (`["Administration", "User Settings"]`)
- `authorization-scheme == "Administration Rights"`
- `name ∈ SYSTEM_PAGE_NAMES` (`["Global Page", "Login Page"]`)

> **Uwaga:** Wcześniejsza heurystyka „wszystkie build-options zaczynają się od Feature:" okazała się nieefektywna — w praktyce strony użytkownika nie mają build-options na poziomie strony, a standardowe strony APEX są już wyłapywane przez page-group i authorization-scheme. Heurystyka usunięta.

### Filtrowanie kluczy YAML (szum do usunięcia)

```python
SKIP_YAML_KEYS = [
    "accessibility",
    "customization",
    "server-cache",
    "session-management",
    "advanced.region-display-selector",
    "advanced.exclude-title-from-translation",
    "advanced.enable-duplicate-page-submissions",
    "export-/-printing",
    "subscription",
    "column-filter",
    "enable-users-to",
    "pagination",
    "toolbar",
    "icon-view",
    "detail-view",
    "saved-reports",
    "download",
    "heading.fixed-to",
]
```

### Filtrowanie wartości

Domyślnie usuwane:
- Wewnętrzne ID APEX (np. `52840988022029242`)
- Template options (`#DEFAULT#`, `t-Region--scrollBody`)
- Layout details (`sequence`, `slot`, `column-span`, `start-new-row`)

Przywracane flagami: `--include-internal-ids`, `--include-layout`.

### Zachowywane zawsze

- Nazwy, typy, aliasy stron/regionów/kolumn
- Tytuły regionów (user-visible labels)
- Źródła danych (tabela, SQL, kolumna)
- Linki między stronami (nawigacja)
- Kod PL/SQL i JavaScript (w tym page-level CSS/JS)
- Warunki (conditions)
- LOV-y przypisane do pól (wszystkie typy: tabelowe, SQL, statyczne)
- Wartości domyślne
- Informacja o edytowalności regionów (IG edit enabled + allowed operations)
- Klucze główne kolumn

### Shared components — zakres

| Komponent | Uwzględniony | Uzasadnienie |
|---|---|---|
| `lovs.yaml` | Tak | Relacje między polami a tabelami |
| `authorizations.yaml` | Tak | Schematy uprawnień z kodem PL/SQL |
| `lists.yaml` | Tak | Struktura nawigacji |
| `app_items.yaml` | Tak | Zmienne sesji globalne |
| `build_options.yaml` | Tak | Używane w heurystykach filtrowania |
| `breadcrumbs.yaml` | Tak | Nawigacja page-to-page |
| `acl_roles.yaml` | Tak | Definicje ról (Administrator, Contributor, Reader) |
| `authentications.yaml` | Nie | Szczegóły ADFS — zbyt techniczne, mało przydatne dla LLM |
| `search_configs.yaml` | Nie | Konfiguracje wyszukiwania — niska wartość informacyjna |
| `theme_42/` | Nie | Czysto wizualne (CSS, szablony) |
| `app_static_files.yaml` | Nie | Pliki statyczne — binaria/CSS, nieprzydatne jako tekst |

## Obsługa błędów

- **Niepoprawny YAML:** Loguj ostrzeżenie, pomiń plik, kontynuuj przetwarzanie
- **Brakujący klucz:** Użyj wartości domyślnej (`None`, `[]`, `False`), nie przerywaj
- **Referencja do nieistniejącego komponentu:** Zachowaj jako tekst (np. nazwa LOV), nie waliduj istnienia
- **Przy `--verbose`:** Loguj każdy pominięty plik i każdy brakujący klucz

## Renderery

### Human Renderer — przykład wyjścia

```markdown
# Aplikacja SKW_TO_APEX (ID: 160, alias: START338)

## Strony użytkownika

### Strona 4: DAW_LISTA_AUDYTOW
- **Tryb:** Normal
- **Bezpieczeństwo:** Page Requires Authentication

#### Region: ListaAudytow — "Lista audytów"
- **Typ:** Interactive Grid (edytowalny: Add Row, Update Row, Delete Row)
- **Źródło:** tabela `B_AUDYT`

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ID_PK_B_AUDYT | Hidden | — | B_AUDYT.ID_PK_B_AUDYT | tak | — |
| B_AUDYT_NUMER_AUDYTU | Link | Numer Audytu | B_AUDYT.B_AUDYT_NUMER_AUDYTU | — | →strona 6 |

#### Procesy
```plsql
-- Nazwa: Zapisz_Dane (After Submit, język: PL/SQL, przycisk: SAVE)
BEGIN PKG_AUDYT.ZAPISZ(...); END;
\```

#### CSS strony
```css
.highlight-row { background: #fef3cd; }
\```

---

## Shared Components

### LOV: B_AUDYT.B_AUDYT_NUMER_AUDYTU
- **Typ źródła:** Table / View
- **Tabela:** B_AUDYT
- **Return:** ID_PK_B_AUDYT
- **Display:** B_AUDYT_NUMER_AUDYTU

### LOV: B_LISTA_KONTROLI_DO_AUDYTU
- **Typ źródła:** SQL Query
- **SQL:** `SELECT ... FROM B_KONTROLA WHERE ...`

### LOV: B_SL_C_ODPOWIEDZ
- **Typ źródła:** Static Values
- **Wartości:** Tak→1, Nie→0, N/A→-1
```

### LLM Renderer — przykład wyjścia

```
APP:160|START338|SKW_TO_APEX
===PAGE:4|DAW_LISTA_AUDYTOW|Normal|auth:required
CSS:inline
.highlight-row { background: #fef3cd; }
---
RGN:ListaAudytow|title:Lista audytów|InteractiveGrid|src:B_AUDYT|edit:true|ops:Add,Update,Delete
COL:ID_PK_B_AUDYT|Hidden|pk:true
COL:B_AUDYT_NUMER_AUDYTU|Link|heading:Numer Audytu|link:page6
ITEM:P4_FILTR_STATUS|SelectList|lov:STATUS_AUDYTU
BTN:UTWORZ_AUDYT|label:Nowy audyt|action:Submit Page|hot:true
PROC:Zapisz_Dane|Execute Code|lang:PLSQL|point:AfterSubmit|btn:SAVE
```plsql
PKG_AUDYT.ZAPISZ(...);
\```
DA:Zmiana_statusu|event:change|sel:Item|trigger:P4_STATUS|scope:Dynamic
DA_STEP:Execute PL/SQL Code|affects:#region1
```plsql
...
\```
BRANCH:Page or URL (Redirect)->page:6|cond:REQUEST=SAVE
===LOV:B_AUDYT.B_AUDYT_NUMER_AUDYTU|type:Table|tbl:B_AUDYT|ret:ID_PK_B_AUDYT|disp:B_AUDYT_NUMER_AUDYTU
===LOV:B_LISTA_KONTROLI|type:SQL
```sql
SELECT ... FROM B_KONTROLA WHERE ...
\```
===LOV:B_SL_C_ODPOWIEDZ|type:Static|Tak:1|Nie:0|N/A:-1
===AUTH:Administration Rights|type:Is In Role|role:Administrator
===BUILD_OPT:Feature: Access Control|status:Include
===BREADCRUMB:Breadcrumb|Home->page:1|Audyty->page:4|Kontrole->page:6
===ACL:Administrator|static_id:ADMINISTRATOR
```

## CLI

```bash
python apex_export_to_md.py <ścieżka_do_exportu> [opcje]

Opcje:
  --output-dir DIR                      # katalog wyjściowy (domyślnie: bieżący)
  --output-prefix PREFIX                # prefiks nazw plików (domyślnie: apex_export)
  --format {both,human,llm}             # które pliki generować (domyślnie: both)
  --include-code {full,summary,none}    # bloki PL/SQL/JS (domyślnie: full)
  --page-filter {auto,all,prefix:X,ids:1,2,3}  # filtr stron (domyślnie: auto)
  --extra-pages 1,9999                  # dodatkowe strony do dołączenia
  --include-internal-ids                # zachowaj ID wewnętrzne APEX
  --include-layout                      # zachowaj szczegóły layoutu
  --no-shared-components                # pomiń shared components
  --verbose                             # szczegółowe logi
```

### Pliki wyjściowe

```
{prefix}_human.md    # czytelny dla człowieka
{prefix}_llm.md      # zoptymalizowany dla LLM
```

Domyślny prefix: `apex_export`.

## Zależności

- Python 3.10+
- `PyYAML` — jedyna zewnętrzna biblioteka
- `argparse` — stdlib

## Zasady implementacji

- Komentarze w kodzie po polsku
- Każdy przełącznik konfigurowalny z CLI lub `config.py`
- Kod przygotowany pod rozbudowę (nowe renderery, nowe filtry)
- Dataclasses jako modele — łatwe do serializacji i inspekcji
- Graceful degradation: pominięte pliki/klucze logowane, nie przerywają przetwarzania
