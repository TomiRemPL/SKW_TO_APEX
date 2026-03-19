# APEX Export to Markdown Converter

Narzędzie wiersza poleceń w Pythonie, które konwertuje eksport aplikacji Oracle APEX (format YAML readable) na czytelne pliki Markdown — w dwóch wariantach: dla człowieka i dla LLM.

---

## Spis treści

1. [Opis projektu](#opis-projektu)
2. [Wymagania](#wymagania)
3. [Instalacja](#instalacja)
4. [Szybki start](#szybki-start)
5. [Dokumentacja CLI](#dokumentacja-cli)
6. [Przypadki użycia](#przypadki-użycia)
7. [Format wyjściowy — human](#format-wyjściowy--human)
8. [Format wyjściowy — LLM](#format-wyjściowy--llm)
9. [Architektura](#architektura)
10. [Heurystyki filtrowania stron](#heurystyki-filtrowania-stron)
11. [Konfiguracja](#konfiguracja)
12. [Rozbudowa](#rozbudowa)
13. [Testy](#testy)
14. [Znane ograniczenia](#znane-ograniczenia)
15. [Licencja](#licencja)

---

## Opis projektu

**Po co?** Eksporty APEX w formacie YAML readable są przydatne do kontroli wersji, ale trudne do przeglądania. To narzędzie przekształca je w Markdown, który:

- jest czytelny bezpośrednio w edytorze lub przeglądarce GitLab/GitHub,
- może być przekazany do modelu językowego (LLM) jako kontekst przy analizie aplikacji,
- ułatwia code review i dokumentowanie logiki biznesowej.

**Co robi?**

- Parsuje strukturę katalogu eksportu APEX (`pages/`, `shared_components/`)
- Wyodrębnia strony, regiony, kolumny, elementy formularza, przyciski, procesy PL/SQL, akcje dynamiczne, rozgałęzienia, walidacje, LOV-y, schematy autoryzacji, nawigację i role ACL
- Filtruje strony standardowe APEX (administracyjne, logowanie), pozostawiając strony użytkownika
- Generuje dwa pliki Markdown: `*_human.md` (czytelny, z tabelami i nagłówkami) i `*_llm.md` (skondensowany, liniowy)

**Dla kogo?** Dla programistów Oracle APEX, którzy chcą przeglądać strukturę aplikacji lub przekazywać ją do analiz przez AI.

---

## Wymagania

- **Python 3.10** lub nowszy
- **PyYAML >= 6.0**
- Eksport APEX w formacie `readable` (katalog zawierający `pages/` i `shared_components/`)

Opcjonalnie do uruchamiania testów:

- **pytest >= 7.0**

---

## Instalacja

### 1. Sklonuj repozytorium

```bash
git clone <url-repozytorium>
cd SKW_TO_APEX
```

### 2. Utwórz i aktywuj wirtualne środowisko

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat
```

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 4. Weryfikacja instalacji

```bash
python -m apex_export_to_md --help
```

Oczekiwany wynik:

```
usage: apex_export_to_md [-h] [--output-dir OUTPUT_DIR] [--output-prefix OUTPUT_PREFIX]
                         [--format {both,human,llm}] [--include-code {full,summary,none}]
                         [--page-filter PAGE_FILTER] [--extra-pages EXTRA_PAGES]
                         [--include-internal-ids] [--include-layout]
                         [--no-shared-components] [--verbose]
                         input_dir

Konwertuje eksport Oracle APEX (readable YAML) na Markdown.
```

---

## Szybki start

Minimalne polecenie — generuje oba formaty w bieżącym katalogu:

```bash
python -m apex_export_to_md program/readable/application/
```

Po wykonaniu powstaną dwa pliki:

```
apex_export_human.md   # format czytelny dla człowieka
apex_export_llm.md     # format skondensowany dla LLM
```

---

## Dokumentacja CLI

### Składnia

```
python -m apex_export_to_md <input_dir> [opcje]
```

### Argumenty pozycyjne

| Argument | Opis |
|----------|------|
| `input_dir` | Ścieżka do katalogu eksportu APEX. Może to być katalog `application/` zawierający bezpośrednio `pages/`, lub katalog nadrzędny — narzędzie samo znajdzie właściwy podkatalog metodą rekursywną. |

### Opcje

#### `--output-dir DIR`

Katalog, do którego zostaną zapisane pliki wyjściowe.

- **Domyślnie:** `.` (bieżący katalog)
- **Przykład:** `--output-dir ./docs/apex`

---

#### `--output-prefix PREFIKS`

Prefiks nazw plików wyjściowych. Narzędzie doda do niego `_human.md` lub `_llm.md`.

- **Domyślnie:** `apex_export`
- **Przykład:** `--output-prefix skw_v2` → pliki `skw_v2_human.md`, `skw_v2_llm.md`

---

#### `--format {both|human|llm}`

Które pliki generować.

| Wartość | Opis |
|---------|------|
| `both` | Generuj oba formaty (domyślnie) |
| `human` | Tylko `*_human.md` — nagłówki, tabele, bloki kodu |
| `llm` | Tylko `*_llm.md` — format liniowy, minimalistyczny |

- **Domyślnie:** `both`
- **Przykład:** `--format llm`

---

#### `--include-code {full|summary|none}`

Jak traktować bloki kodu PL/SQL i JavaScript.

| Wartość | Opis |
|---------|------|
| `full` | Dołącz pełny kod w blokach ` ```sql ` / ` ```plsql ` / ` ```javascript ` (domyślnie) |
| `summary` | Tylko pierwsza linia kodu z wielokropkiem: `` > `SELECT * FROM B_OCENA...` `` |
| `none` | Całkowicie pomiń kod — tylko metadane |

- **Domyślnie:** `full`
- **Przykład:** `--include-code summary`

---

#### `--page-filter FILTR`

Tryb filtrowania stron. Obsługuje cztery formy:

| Forma | Opis | Przykład |
|-------|------|---------|
| `auto` | Heurystyki: pomija strony administracyjne i systemowe (domyślnie) | `--page-filter auto` |
| `all` | Wszystkie strony bez filtrowania | `--page-filter all` |
| `prefix:X` | Tylko strony, których nazwa zaczyna się od `X` | `--page-filter prefix:DAW_` |
| `ids:1,2,3` | Tylko strony o podanych ID | `--page-filter ids:2,3,10` |

- **Domyślnie:** `auto`
- **Przykład:** `--page-filter prefix:DAW_`

---

#### `--extra-pages ID1,ID2,...`

Lista dodatkowych ID stron do dołączenia — niezależnie od filtra. Przydatne gdy `prefix:DAW_` nie obejmuje np. strony Home (ID=1).

- **Domyślnie:** *(pusta)*
- **Przykład:** `--extra-pages 1,9999`

---

#### `--include-internal-ids`

Flaga (bez wartości). Zachowuje wewnętrzne ID APEX w strukturach YAML (domyślnie są usuwane przez `strip_apex_id`).

- **Domyślnie:** wyłączone
- **Przykład:** `--include-internal-ids`

---

#### `--include-layout`

Flaga (bez wartości). Zachowuje szczegóły layoutu (pozycje, kolumny siatki).

- **Domyślnie:** wyłączone
- **Przykład:** `--include-layout`

---

#### `--no-shared-components`

Flaga (bez wartości). Pomija sekcję Shared Components (LOV-y, autoryzacje, nawigacja, role ACL itp.).

- **Domyślnie:** shared components są dołączane
- **Przykład:** `--no-shared-components`

---

#### `--verbose`

Flaga (bez wartości). Włącza szczegółowe logi (poziom DEBUG) — pokazuje m.in. które strony są pomijane i dlaczego.

- **Domyślnie:** wyłączone (poziom INFO)
- **Przykład:** `--verbose`

---

## Przypadki użycia

### 1. Podstawowe użycie — oba formaty

Generuje `apex_export_human.md` i `apex_export_llm.md` w bieżącym katalogu.

```bash
python -m apex_export_to_md program/readable/application/
```

---

### 2. Tylko format LLM

Generuje wyłącznie skondensowany plik dla modeli językowych. Przydatne gdy chcesz przekazać kontekst do ChatGPT/Claude.

```bash
python -m apex_export_to_md program/readable/application/ --format llm
```

---

### 3. Tylko format human

Generuje wyłącznie plik czytelny dla człowieka — np. do code review lub dokumentacji.

```bash
python -m apex_export_to_md program/readable/application/ --format human
```

---

### 4. Filtrowanie po prefiksie nazwy stron

Aplikacja SKW_TO_APEX ma strony biznesowe z prefiksem `DAW_`. Generuje dokumentację tylko tych stron:

```bash
python -m apex_export_to_md program/readable/application/ --page-filter prefix:DAW_
```

---

### 5. Filtrowanie po ID stron

Generuje dokumentację konkretnych stron — np. ankieta (2), lista audytów (3), szczegóły audytu (4):

```bash
python -m apex_export_to_md program/readable/application/ --page-filter ids:2,3,4
```

---

### 6. Tryb all — wszystkie strony

Dołącza też strony standardowe APEX (Login Page, strony administracyjne). Przydatne do pełnego audytu aplikacji.

```bash
python -m apex_export_to_md program/readable/application/ --page-filter all
```

---

### 7. Dodanie dodatkowych stron do filtra prefix

Strona `Home` (ID=1) nie zaczyna się od `DAW_`, ale chcemy ją dołączyć:

```bash
python -m apex_export_to_md program/readable/application/ \
  --page-filter prefix:DAW_ \
  --extra-pages 1
```

---

### 8. Bez shared components

Generuje tylko strony, pomijając LOV-y, autoryzacje i nawigację. Przydatne gdy interesuje Cię wyłącznie logika stron:

```bash
python -m apex_export_to_md program/readable/application/ --no-shared-components
```

---

### 9. Bez kodu PL/SQL — tylko metadane

Generuje najkrótszy możliwy plik — tylko typy, nazwy i struktury, bez żadnego kodu:

```bash
python -m apex_export_to_md program/readable/application/ --include-code none
```

---

### 10. Tryb summary kodu

Kod jest zastępowany pierwszą linią z wielokropkiem. Kompromis między czytelnością a rozmiarem pliku:

```bash
python -m apex_export_to_md program/readable/application/ --include-code summary
```

Fragment wyjścia w trybie summary:

```
> `SELECT * FROM B_OCENA a...`
```

---

### 11. Zachowanie wewnętrznych ID APEX

Domyślnie ID APEX (np. `12345678901234.00`) są usuwane ze struktur. Ta opcja je zachowuje:

```bash
python -m apex_export_to_md program/readable/application/ --include-internal-ids
```

---

### 12. Zmiana prefiksu pliku wyjściowego

Generuje `skw_dokumentacja_human.md` i `skw_dokumentacja_llm.md` w katalogu `docs/`:

```bash
python -m apex_export_to_md program/readable/application/ \
  --output-dir docs/ \
  --output-prefix skw_dokumentacja
```

---

### 13. Pełny verbose z wszystkimi opcjami

Kompletne wywołanie z logowaniem DEBUG — widać każdą pominiętą stronę i etapy pipeline'u:

```bash
python -m apex_export_to_md program/readable/application/ \
  --output-dir ./docs/apex \
  --output-prefix skw_v2 \
  --format both \
  --include-code full \
  --page-filter prefix:DAW_ \
  --extra-pages 1 \
  --no-shared-components \
  --verbose
```

Przykładowe logi:

```
INFO: Katalog aplikacji: program/readable/application
INFO: Sparsowano 35 stron
DEBUG: Pomijam stronę standardową: Administration (ID=10000)
DEBUG: Pomijam stronę standardową: Login Page (ID=9999)
INFO: Po filtracji: 12 stron
INFO: Zapisano: docs/apex/skw_v2_human.md (48320 znaków)
INFO: Zapisano: docs/apex/skw_v2_llm.md (18750 znaków)
```

---

## Format wyjściowy — human

Plik `*_human.md` używa standardowego Markdown z nagłówkami, tabelami i blokami kodu. Przeznaczony do przeglądania w edytorze lub przeglądarce.

### Struktura dokumentu

```
# Aplikacja <nazwa> (ID: <id>, alias: <alias>)

## Strony użytkownika

### Strona <ID>: <nazwa>
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: <nazwa> — "<tytuł>"
- **Typ:** Interactive Grid (edytowalny: Update Row, Delete Row)
- **Źródło SQL:**
```sql
SELECT ...
```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ...     | ... | ...      | ...    | .. | ...  |

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| ...   | ... | ...      | ...     | ... |

#### Przyciski

- **ZAPISZ** — Zapisz [Submit Page] **(primary)**

#### Procesy

**Aktualizacja audytu** (After Submit, język: PL/SQL, przycisk: ZAPISZ)

```plsql
PKG_AUDYT.ZAKONCZ_AUDYT(p_audyt_id => :P4_ID_PK_B_AUDYT);
```

---

## Shared Components

### Listy wartości (LOV)
### Schematy autoryzacji
### Listy nawigacyjne
### Zmienne globalne
### Role ACL
```

### Przykład rzeczywisty (fragment z SKW_TO_APEX)

```markdown
# Aplikacja SKW_2_APEX (ID: 160, alias: START338)

## Strony użytkownika

### Strona 2: DAW_ANKIETA
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: P2_SKUTECZNOSC_OCENA
- **Typ:** Interactive Grid (edytowalny: Update Row)
- **Źródło SQL:**
```sql
SELECT * FROM B_OCENA a
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 2 /*skuteczność*/
```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| B_OCENA_LICZONA | Number Field | Ocena wyliczona: | B_OCENA_LICZONA | — | — |
| ID_PK_B_OCENA | Hidden | — | ID_PK_B_OCENA | tak | — |
```

---

## Format wyjściowy — LLM

Plik `*_llm.md` używa skondensowanego formatu liniowego, zoptymalizowanego pod minimalizację liczby tokenów. Każdy obiekt APEX jest reprezentowany przez jeden lub kilka wierszy z prefiksem typu i wartościami oddzielonymi znakiem `|`.

### Prefiksy typów

| Prefiks | Znaczenie |
|---------|-----------|
| `APP:` | Nagłówek aplikacji |
| `===PAGE:` | Nowa strona (separator `===`) |
| `RGN:` | Region |
| `COL:` | Kolumna regionu |
| `ITEM:` | Element formularza |
| `BTN:` | Przycisk |
| `PROC:` | Proces serwerowy |
| `DA:` | Akcja dynamiczna |
| `DA_STEP:` | Krok akcji dynamicznej |
| `BRANCH:` | Rozgałęzienie nawigacyjne |
| `VAL:` | Walidacja |
| `CSS:inline` | Inline CSS |
| `JS:inline` | Inline JavaScript |
| `===LOV:` | Lista wartości |
| `===AUTH:` | Schemat autoryzacji |
| `===NAV:` | Lista nawigacyjna |
| `===APP_ITEM:` | Zmienna globalna |
| `===BUILD_OPT:` | Opcja budowania |
| `===BREADCRUMB:` | Breadcrumb |
| `===ACL:` | Rola ACL |

### Konwencje

- Linie z `===` oznaczają nowy główny obiekt (strona, shared component)
- Atrybuty mają formę `klucz:wartość`
- Bloki kodu są osadzone standardowo w ` ```sql ``` `, ` ```plsql ``` ` itp.
- `ENTRIES:` dla LOV-ów ze statycznymi wartościami używa formatu `display:return|display:return`

### Przykład rzeczywisty (fragment z SKW_TO_APEX)

```
APP:160|START338|SKW_2_APEX
===PAGE:1|Home|Normal|auth:required
RGN:My Info|Static Content
RGN:Copyright|Static Content
RGN:Tytuł|title:SKW_2_APEX by DAW|Static Content
===PAGE:2|DAW_ANKIETA|Normal|auth:required
CSS:inline
.tekst-zawijany {
    white-space: pre-wrap !important;
}
---
RGN:P2_SKUTECZNOSC_OCENA|Interactive Grid|src:SQL|edit:true|ops:Update
```sql
SELECT * FROM B_OCENA a
WHERE 1=1
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 2 /*skuteczność*/
```
COL:B_OCENA_LICZONA|Number Field|heading:Ocena wyliczona:
COL:ID_PK_B_OCENA|Hidden|pk:true
ITEM:P2_AUDYT_ID|Hidden|col:ID_PK_B_AUDYT
BTN:ZAPISZ|label:Zapisz|action:Submit Page|hot:true
PROC:Aktualizacja audytu|Execute Code|lang:PL/SQL|point:After Submit|btn:ZAPISZ
```plsql
PKG_AUDYT.ZAKONCZ_AUDYT(p_audyt_id => :P4_ID);
```
===LOV:B_SL_C_ODPOWIEDZ|type:Table|tbl:B_SL_C_ODPOWIEDZ|ret:ID_PK|disp:ODPOWIEDZ
===AUTH:Audytor|type:PL/SQL Function Body
===ACL:Contributor|static_id:CONTRIBUTOR
```

---

## Architektura

### Pipeline przetwarzania

```
input_dir/
    f*.yaml          (definicja aplikacji)
    pages/
        p00001.yaml
        p00002.yaml
        ...
    shared_components/
        ...

         |
         v
  [find_app_root]   -- wykrywa katalog application/ rekursywnie
         |
         v
  [parse_app_definition]  -- app name, ID, alias z f*.yaml
         |
         v
  [parse_all_pages]       -- parsuje pages/p*.yaml → lista ApexPage
         |
         v
  [PageFilter.filter_pages]  -- filtruje wg page_filter + extra_pages
         |
         v
  [parse_shared_components]  -- LOV-y, auth, nav, app_items, ACL...
         |
         v
  [ApexApp]              -- agregat wszystkich danych
         |
       /   \
      v     v
[HumanRenderer] [LLMRenderer]
      |           |
      v           v
*_human.md    *_llm.md
```

### Moduły

| Moduł | Plik | Odpowiedzialność |
|-------|------|-----------------|
| `cli.py` | `apex_export_to_md/cli.py` | Parsowanie argumentów CLI, orkiestracja pipeline'u |
| `config.py` | `apex_export_to_md/config.py` | Dataclass `AppConfig`, stałe heurystyk |
| `models/apex_models.py` | `models/` | Dataclassy: `ApexApp`, `ApexPage`, `Region`, `Column`, `Process` itp. |
| `parser/page_parser.py` | `parser/` | Parsowanie `pages/p*.yaml` → `ApexPage` |
| `parser/shared_parser.py` | `parser/` | Parsowanie `shared_components/` → LOV, Auth, Nav itp. |
| `parser/yaml_helpers.py` | `parser/` | Pomocnicze funkcje YAML: `safe_get`, `strip_apex_id`, `collect_build_options` |
| `filters/page_filter.py` | `filters/` | Klasa `PageFilter` — logika wszystkich trybów filtrowania |
| `renderers/base_renderer.py` | `renderers/` | ABC `BaseRenderer` — interfejs + pomocnicze metody kodu |
| `renderers/human_renderer.py` | `renderers/` | Markdown z nagłówkami, tabelami i blokami kodu |
| `renderers/llm_renderer.py` | `renderers/` | Format liniowy `PREFIX:wartość\|...` |

---

## Heurystyki filtrowania stron

W trybie `auto` program odróżnia strony użytkownika od standardowych stron APEX na podstawie trzech heurystyk (zdefiniowanych w `config.py`):

### Heurystyka 1: Grupa strony (`page_group`)

Strony należące do którejkolwiek z grup na liście `STANDARD_PAGE_GROUPS` są pomijane:

```python
STANDARD_PAGE_GROUPS = [
    "Administration",
    "User Settings",
]
```

### Heurystyka 2: Schemat autoryzacji (`authorization-scheme`)

Strony z schematem autoryzacji równym `STANDARD_AUTH_SCHEME` są pomijane:

```python
STANDARD_AUTH_SCHEME = "Administration Rights"
```

### Heurystyka 3: Znane nazwy systemowe (`SYSTEM_PAGE_NAMES`)

Strony o konkretnych nazwach są zawsze pomijane:

```python
SYSTEM_PAGE_NAMES = [
    "Global Page",
    "Login Page",
]
```

### Kolejność sprawdzania

Heurystyki są sprawdzane w kolejności 1 → 2 → 3. Wystarczy spełnienie jednej, żeby strona została pominięta. Strony spoza tej listy i strony z `extra_pages` zawsze trafiają do wyniku.

---

## Konfiguracja

Plik `apex_export_to_md/config.py` zawiera dwa elementy:

### `AppConfig` — dataclass konfiguracji

Wszystkie pola odpowiadają bezpośrednio opcjom CLI. Wartości domyślne:

```python
output_dir: str = "."
output_prefix: str = "apex_export"
output_format: str = "both"       # "both" | "human" | "llm"
include_code: str = "full"        # "full" | "summary" | "none"
page_filter: str = "auto"         # "auto" | "all" | "prefix:X" | "ids:1,2,3"
extra_pages: list[int] = []
include_internal_ids: bool = False
include_layout: bool = False
include_shared_components: bool = True
verbose: bool = False
```

### Stałe heurystyk filtrowania

Aby rozszerzyć logikę `auto`, zmodyfikuj stałe w `config.py`:

- **`STANDARD_PAGE_GROUPS`** — dodaj nazwy grup stron do pominięcia
- **`STANDARD_AUTH_SCHEME`** — zmień nazwę schematu autoryzacji "administracyjnego"
- **`SYSTEM_PAGE_NAMES`** — dodaj nazwy stron systemowych

### `SKIP_YAML_KEYS` i `SKIP_NESTED_KEYS`

Listy kluczy YAML, które są odfiltrowane jako "szum" podczas parsowania (np. `accessibility`, `pagination`, `toolbar`). Modyfikacja tych list pozwala dołączyć lub wykluczyć dodatkowe pola z eksportu APEX.

---

## Rozbudowa

### Dodanie nowego renderera (np. JSON lub HTML)

1. Utwórz plik `apex_export_to_md/renderers/json_renderer.py`
2. Stwórz klasę dziedziczącą po `BaseRenderer`:

```python
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp

class JsonRenderer(BaseRenderer):
    def render(self, app: ApexApp) -> str:
        import json
        # ... buduj strukturę słownikową z app.pages, app.lovs itp.
        return json.dumps(data, ensure_ascii=False, indent=2)
```

3. W `cli.py`, w funkcji `run_pipeline`, dodaj obsługę nowego formatu:

```python
if config.output_format in ("both", "json"):
    renderer = JsonRenderer(config)
    content = renderer.render(app)
    out_path = output_dir / f"{config.output_prefix}.json"
    out_path.write_text(content, encoding="utf-8")
```

4. Dodaj `"json"` do listy `choices` argumentu `--format` w `parse_args`.

### Dodanie nowego filtra stron

Aby dodać tryb `group:Administration`:

1. W `PageFilter.filter_pages` dodaj nowy `elif`:

```python
elif self._mode == "group":
    group_name = self._param
    return [p for p in pages if p.page_group == group_name or p.id in extra_ids]
```

Logika `_parse_filter_spec` automatycznie obsłuży format `group:Administration`.

### Dodanie nowego parsera obiektów APEX

Nowe typy obiektów APEX (np. Computation, Plugin) dodaje się w trzech krokach:

1. Dodaj dataclass w `models/apex_models.py`
2. Dodaj logikę parsowania w `parser/page_parser.py` lub `parser/shared_parser.py`
3. Dodaj renderowanie w `renderers/human_renderer.py` i `renderers/llm_renderer.py`

---

## Testy

Testy są w katalogu `tests/` i używają `pytest`.

### Uruchomienie wszystkich testów

```bash
pytest tests/
```

### Uruchomienie z verbose output

```bash
pytest tests/ -v
```

### Uruchomienie konkretnego modułu testów

```bash
pytest tests/test_page_filter.py -v
pytest tests/test_human_renderer.py -v
pytest tests/test_llm_renderer.py -v
pytest tests/test_integration.py -v
```

### Pokrycie kodu (opcjonalnie)

```bash
pip install pytest-cov
pytest tests/ --cov=apex_export_to_md --cov-report=term-missing
```

### Struktura testów

| Plik | Co testuje |
|------|-----------|
| `test_config.py` | `AppConfig` — wartości domyślne i pola |
| `test_models.py` | Dataclassy modelu APEX |
| `test_yaml_helpers.py` | Funkcje pomocnicze parsera YAML |
| `test_page_parser.py` | Parsowanie plików `pages/p*.yaml` |
| `test_shared_parser.py` | Parsowanie `shared_components/` |
| `test_page_filter.py` | Wszystkie tryby `PageFilter` |
| `test_human_renderer.py` | Format human Markdown |
| `test_llm_renderer.py` | Format LLM liniowy |
| `test_cli.py` | Parsowanie argumentów CLI |
| `test_integration.py` | Integracyjny end-to-end pipeline |

---

## Znane ograniczenia

1. **Tylko eksporty YAML readable** — narzędzie nie obsługuje starszego formatu SQL eksportu APEX (pliki `.sql`). Wymaga eksportu z opcją "Readable YAML".

2. **Brak obsługi Master Detail** — relacje parent/child między regionami (Master Detail) są parsowane jako flat lista regionów bez hierarchii.

3. **Częściowe parsowanie procesów API** — procesy typu "Invoke API" (np. wywołania REST) mają ograniczone parsowanie — wyciągany jest tylko typ i punkt wywołania, bez szczegółów parametrów.

4. **Brak parsowania Computations** — elementy APEX Computation (obliczenia wartości itemów) nie są aktualnie wyciągane.

5. **Brak parsowania Page Computations i Application Computations** — podobnie jak Computations na poziomie strony.

6. **LOV-y zagnieżdżone w kolumnach** — LOV przypisany bezpośrednio do kolumny Interactive Grid jest wyciągany tylko przez nazwę; jego definicja SQL nie jest inline rozwijana.

7. **Wewnętrzne ID APEX** — domyślnie są usuwane przez `strip_apex_id`. Opcja `--include-internal-ids` zachowuje je, ale nie jest jeszcze w pełni zaimplementowana we wszystkich parserach.

8. **Duże aplikacje** — przy aplikacjach z setkami stron i pełnym kodem (`--include-code full`) plik `*_human.md` może mieć kilka MB. Dla LLM zalecane jest `--include-code summary` lub `none`.

---

## Licencja

MIT License

Copyright (c) 2024 DAW

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
