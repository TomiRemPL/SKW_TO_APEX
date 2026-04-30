# APEX Export to Markdown Converter

Narzędzie wiersza poleceń w Pythonie, które konwertuje eksport aplikacji Oracle APEX (format YAML readable) na czytelne pliki Markdown — w dwóch wariantach: dla człowieka i dla LLM. Dodatkowo parsuje pliki DDL/PL/SQL i generuje dokumentację schematu bazy danych oraz interaktywną stronę HTML z diagramem relacji.

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
9. [Pipeline DDL — dokumentacja bazy danych](#pipeline-ddl--dokumentacja-bazy-danych)
10. [Interaktywny HTML](#interaktywny-html)
11. [Architektura](#architektura)
12. [Heurystyki filtrowania stron](#heurystyki-filtrowania-stron)
13. [Konfiguracja](#konfiguracja)
14. [Rozbudowa](#rozbudowa)
15. [Testy](#testy)
16. [Znane ograniczenia](#znane-ograniczenia)
17. [Licencja](#licencja)

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
- **Parsuje pliki DDL/PL/SQL** — tabele, widoki, pakiety (spec + body), sekwencje, constrainty, indeksy, komentarze
- **Generuje dokumentację bazy danych** — `*_db_human.md` z diagramem Mermaid ER + `*_db_llm.md` w skondensowanym formacie
- **Wykrywa powiązania APEX↔DB** — automatycznie łączy strony APEX z tabelami/widokami na podstawie heurystyk SQL
- **Generuje interaktywny HTML** — self-contained strona z vis.js (offline), 3 zakładki: diagram relacji, przeglądarka DB, mapa APEX↔DB

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
                         [--no-ddl] [--ddl-files DDL_FILES [DDL_FILES ...]]
                         [--no-html] [--html-output HTML_OUTPUT]
                         [--author-name AUTHOR_NAME]
                         input_dir

Konwertuje eksport Oracle APEX (readable YAML) na Markdown.
```

---

## Szybki start

Minimalne polecenie — generuje oba formaty w bieżącym katalogu:

```bash
python -m apex_export_to_md program/readable/application/
```

Po wykonaniu powstaną pliki (w zależności od wykrytych danych):

```
apex_export_human.md           # APEX — format czytelny dla człowieka
apex_export_llm.md             # APEX — format skondensowany dla LLM
apex_export_db_human.md        # Baza danych — z diagramem Mermaid ER
apex_export_db_llm.md          # Baza danych — skondensowany
apex_export_interactive.html   # Interaktywna strona HTML (vis.js)
```

Pliki `_db_*` i `.html` powstają automatycznie, gdy w katalogu eksportu zostanie wykryty plik `*.sql` z DDL.

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

#### `--no-ddl`

Flaga (bez wartości). Wyłącza pipeline DDL — nie parsuje plików SQL i nie generuje plików `*_db_human.md` / `*_db_llm.md`.

- **Domyślnie:** DDL jest włączony (jeśli wykryto pliki `*.sql`)
- **Przykład:** `--no-ddl`

---

#### `--ddl-files PLIK1 [PLIK2 ...]`

Jawne wskazanie plików DDL/SQL do sparsowania. Jeśli pominięto, narzędzie automatycznie szuka plików `*.sql` w katalogu eksportu i katalogach nadrzędnych.

- **Domyślnie:** automatyczne wykrywanie
- **Przykład:** `--ddl-files schema.sql triggers.sql`

---

#### `--no-html`

Flaga (bez wartości). Wyłącza generowanie interaktywnej strony HTML.

- **Domyślnie:** HTML jest generowany (jeśli sparsowano DDL)
- **Przykład:** `--no-html`

---

#### `--html-output ŚCIEŻKA`

Jawna ścieżka do pliku HTML wyjściowego. Jeśli pominięto, plik powstaje w `output_dir` z sufiksem `_interactive.html`.

- **Domyślnie:** `<output_dir>/<output_prefix>_interactive.html`
- **Przykład:** `--html-output docs/schema_viewer.html`

---

#### `--author-name NAZWA`

Nazwa autora wyświetlana w stopce generowanego pliku HTML.

- **Domyślnie:** `Tomasz Rembiasz`
- **Przykład:** `--author-name "Jan Kowalski"`

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

### 13. Tylko APEX, bez DDL i HTML

Generuje wyłącznie pliki Markdown dla APEX — bez parsowania bazy danych i bez strony HTML:

```bash
python -m apex_export_to_md program/readable/application/ --no-ddl --no-html
```

---

### 14. Wskazanie konkretnego pliku DDL

Narzędzie automatycznie szuka `*.sql`, ale można jawnie podać plik(i):

```bash
python -m apex_export_to_md program/readable/application/ \
  --ddl-files ./SKW_TO_APEX_DDL.sql
```

---

### 15. Zmiana autora w HTML

Domyślny autor to "Tomasz Rembiasz". Aby zmienić:

```bash
python -m apex_export_to_md program/readable/application/ \
  --author-name "Jan Kowalski"
```

---

### 16. Pełny verbose z wszystkimi opcjami

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
  --ddl-files ./SKW_TO_APEX_DDL.sql \
  --author-name "Tomasz Rembiasz" \
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
INFO: Pipeline DDL: sparsowano 1 plik SQL
INFO: Zapisano: docs/apex/skw_v2_db_human.md (32100 znaków)
INFO: Zapisano: docs/apex/skw_v2_db_llm.md (12400 znaków)
INFO: Linker APEX↔DB: wykryto 45 powiązań
INFO: Zapisano: docs/apex/skw_v2_interactive.html (890KB)
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
- **deep-linking:** Application Default
- **page-access-protection:** Arguments Must Have Checksum

<details><summary>Pełne atrybuty strony</summary>

```yaml
appearance:
  page-mode: Normal
  page-template: Theme Default
  template-options:
  - '#DEFAULT#'
dialog:
  width: 480
  chained: false
navigation:
  cursor-focus: Do not focus cursor
  warn-on-unsaved-changes: true
help:
  help-text: |
    <p>Opis strony...</p>
...
```

</details>

#### Region: <nazwa> — "<tytuł>"
- **Typ:** Interactive Grid (edytowalny: Update Row, Delete Row)
- **Źródło SQL:**
```sql
SELECT ...
```

<details><summary>Pełne atrybuty regionu</summary>

```yaml
appearance:
  template: Standard
  template-options:
  - '#DEFAULT#'
  - t-Region--noPadding
  css-classes:
  - margin-sm
accessibility:
  use-landmark: true
server-cache:
  caching: Disabled
configuration:
  build-option: 'Feature: Configuration Options'
attributes:
  layout:
    number-of-rows-type: Static Value
    number-of-rows: 15
  pagination:
    type: No Pagination (Show All Rows)
...
```

</details>

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ...     | ... | ...      | ...    | .. | ...  |

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| ...   | ... | ...      | ...     | ... |
  <details><summary>atrybuty P4_STATUS</summary>
  ```yaml
  settings:
    use-defaults: true
  layout:
    sequence: 30
    slot: BODY
    alignment: Left
    label-column-span: 3
  validation:
    value-required: true
  session-state:
    data-type: VARCHAR2
    storage: Per Session (Persistent)
  security:
    session-state-protection: Unrestricted
  ...
  ```
  </details>

#### Przyciski

- **ZAPISZ** — Zapisz [Submit Page] **(primary)**
  <details><summary>atrybuty</summary>
  ```yaml
  layout:
    sequence: 20
    region: Buttons
    slot: CREATE
  appearance:
    button-template: Text
    template-options:
    - '#DEFAULT#'
  behavior:
    execute-validations: true
    show-processing: false
  ...
  ```
  </details>

#### Procesy

**Aktualizacja audytu** (After Submit, język: PL/SQL, przycisk: ZAPISZ)

```plsql
PKG_AUDYT.ZAKONCZ_AUDYT(p_audyt_id => :P4_ID_PK_B_AUDYT);
```

<details><summary>Pełne atrybuty procesu</summary>

```yaml
execution:
  sequence: 10
error-handling:
  ...
```

</details>

---

## Shared Components
...
```

### Pełne atrybuty obiektów APEX (`raw_attributes`)

Każdy obiekt APEX w pliku wyjściowym zawiera sekcję **Pełne atrybuty** w rozwijanym bloku `<details>`. Sekcja ta zawiera kompletną strukturę YAML obiektu z pliku eksportu APEX, po oczyszczeniu z wewnętrznych ID.

**Co jest zawarte w `raw_attributes`:**

- `appearance.*` — template, template-options, css-classes, render-components
- `layout.*` — sequence, slot, column-span, start-new-row, label-column-span
- `settings.*` — parametry specyficzne dla typu obiektu
- `validation.*` — value-required itp.
- `advanced.*` — warn-on-unsaved-changes, region-display-selector
- `session-state.*` — data-type, storage
- `security.*` — session-state-protection, escape-special-characters
- `help.*` — help-text, inline-help-text
- `configuration.*` — build-option
- `server-cache.*` — caching
- `accessibility.*` — use-landmark, landmark-type
- `customization.*` — customizable
- `dialog.*` — width, chained, resizable (dla stron modalnych)
- `navigation.*` — cursor-focus, warn-on-unsaved-changes
- `attributes.*` — atrybuty specyficzne dla typu regionu (chart, pagination, layout itp.)

**Co NIE jest zawarte** (bo wyekstrahowane jawnie do pól modelu):
- `identification.name`, `identification.type`, `identification.title` — → pola `name`, `type`, `title`
- `source.table-name`, `source.sql-query` — → pola `source_table`, `source_sql`
- `id` — wewnętrzny ID APEX (zawsze usuwany)

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
| `PAGE_ATTRS:` | Pełne atrybuty strony (spłaszczone) |
| `RGN:` | Region |
| `RGN_ATTRS:` | Pełne atrybuty regionu (spłaszczone) |
| `COL:` | Kolumna regionu |
| `COL_ATTRS:` | Pełne atrybuty kolumny (spłaszczone) |
| `ITEM:` | Element formularza |
| `ITEM_ATTRS:` | Pełne atrybuty elementu (spłaszczone) |
| `BTN:` | Przycisk |
| `BTN_ATTRS:` | Pełne atrybuty przycisku (spłaszczone) |
| `PROC:` | Proces serwerowy |
| `PROC_ATTRS:` | Pełne atrybuty procesu (spłaszczone) |
| `DA:` | Akcja dynamiczna |
| `DA_ATTRS:` | Pełne atrybuty akcji dynamicznej (spłaszczone) |
| `DA_STEP:` | Krok akcji dynamicznej |
| `DA_STEP_ATTRS:` | Pełne atrybuty kroku DA (spłaszczone) |
| `BRANCH:` | Rozgałęzienie nawigacyjne |
| `BRANCH_ATTRS:` | Pełne atrybuty brancha (spłaszczone) |
| `VAL:` | Walidacja |
| `VAL_ATTRS:` | Pełne atrybuty walidacji (spłaszczone) |
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
- Linie `*_ATTRS:` zawierają pełne atrybuty obiektu w formacie spłaszczonym: `klucz=wartosc;klucz.zagniezdzony=wartosc` — np. `PAGE_ATTRS:appearance.page-mode=Normal;appearance.page-template=Theme Default;dialog.width=480`

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

## Pipeline DDL — dokumentacja bazy danych

Pipeline DDL automatycznie parsuje pliki `*.sql` zawierające definicje DDL i PL/SQL, generując dokumentację schematu bazy danych.

### Wykrywanie plików SQL

Narzędzie szuka plików `*.sql` w następujących lokalizacjach (w kolejności):
1. Katalog eksportu APEX (`input_dir`)
2. Katalogi nadrzędne (do 3 poziomów w górę)
3. Jawnie wskazane pliki (opcja `--ddl-files`)

### Co jest parsowane

| Obiekt | Źródło DDL | Przykład |
|--------|-----------|---------|
| Tabele | `CREATE TABLE` | Kolumny, typy danych, wartości domyślne, NOT NULL |
| Constrainty | `ALTER TABLE ADD CONSTRAINT` | PK, FK (z tabelą referencyjną), UNIQUE, CHECK |
| Indeksy | `CREATE INDEX` / `CREATE UNIQUE INDEX` | Nazwy, kolumny, unikalność |
| Widoki | `CREATE OR REPLACE VIEW` | Kolumny (z SELECT), pełne SQL |
| Pakiety | `CREATE OR REPLACE PACKAGE [BODY]` | Spec + body merge, podprogramy (public/private) |
| Sekwencje | `CREATE SEQUENCE` | Nazwa |
| Komentarze | `COMMENT ON TABLE/COLUMN` | Komentarze tabel i kolumn |

### Obsługa PL/SQL

Parser obsługuje pełne pakiety PL/SQL:
- **Spec** — wyodrębniane procedury i funkcje z sygnaturami
- **Body** — zachowane źródło, prywatne podprogramy oznaczane jako `private`
- **Merge** — spec i body tego samego pakietu łączone w jeden obiekt `DbPackage`

Bloki PL/SQL są dzielone separatorem `/` (poza stringami), a bloki DDL separatorem `;`.

### Format wyjściowy — DB Human (`*_db_human.md`)

Zawiera:
- Nagłówek z nazwą schematu
- **Diagram Mermaid ER** — relacje FK między tabelami, automatycznie wygenerowany
- Sekcje dla każdej tabeli: kolumny (tabela MD), constrainty, indeksy, komentarze
- Sekcje widoków z kolumnami i SQL
- Sekcje pakietów z podprogramami (public i private)
- Lista sekwencji

### Format wyjściowy — DB LLM (`*_db_llm.md`)

Skondensowany format liniowy z prefiksami:

| Prefiks | Znaczenie |
|---------|-----------|
| `SCHEMA:DB` | Nagłówek schematu |
| `TBL:<nazwa>` | Tabela |
| `COL:<nazwa>\|<typ>` | Kolumna tabeli |
| `CONSTRAINT:<typ>` | Constraint |
| `IDX:<nazwa>` | Indeks |
| `VW:<nazwa>` | Widok |
| `PKG:<nazwa>` | Pakiet |
| `SUB:<nazwa>` | Podprogram pakietu |
| `SEQ:<nazwa>` | Sekwencja |

---

## Interaktywny HTML

Narzędzie generuje self-contained stronę HTML z interaktywnym widokiem schematu bazy danych i powiązań z APEX. Plik nie wymaga połączenia z internetem — biblioteka **vis.js 9.1.6** jest osadzona inline.

### 3 zakładki

1. **Diagram relacji** — interaktywny graf vis.js Network:
   - Węzły = tabele i widoki
   - Krawędzie = relacje FK (z etykietami nazw constraintów)
   - Fizyka symulacji (siły sprężystości) — drag & drop, zoom, pan
   - Kolory: tabele (niebieski), widoki (zielony)

2. **Baza danych** — przeglądarka schematu:
   - Drzewo tabel/widoków/pakietów/sekwencji (panel lewy)
   - Panel szczegółów (prawy): kolumny, constrainty, indeksy, komentarze, podprogramy
   - Klikanie w drzewo otwiera szczegóły obiektu

3. **APEX↔DB** — mapa powiązań i pełne atrybuty:
   - Lewa kolumna: strony APEX i shared components (LOV-y)
   - Prawa kolumna: obiekty bazy danych (tabele, widoki, pakiety)
   - **Dwukierunkowe podświetlanie**: kliknięcie strony APEX podświetla powiązane obiekty DB i odwrotnie
   - Źródła powiązań: `region` (SQL/tabela), `process` (kod PL/SQL), `validation`, `lov`
   - **Panel szczegółów strony** z rozwijanymi sekcjami (Regiony, Elementy, Przyciski, Procesy, DA, Walidacje, Branching)
   - **Pełne atrybuty każdego obiektu** w rozwijanych panelach `<details>` z formatowaniem YAML (funkcja JS `renderRawAttrs` + `formatAttrsYaml`)

### Heurystyki linkera APEX↔DB

Linker (`ApexDbLinker`) wykrywa powiązania automatycznie:
- Skanuje SQL regionów, kod procesów, wyrażenia walidacji, SQL LOV-ów
- Szuka nazw tabel, widoków i pakietów jako **całych słów** (word boundary regex)
- Dopasowuje **longest-first** — aby `B_AUDYT_KONTROLA` nie było fałszywie dopasowane jako `B_AUDYT`
- Obsługuje `source_table` regionów i LOV-ów (bezpośrednie referencje bez SQL)
- Case-insensitive matching

### Branding

- Logo SVG z inicjałami "TR" w nagłówku
- Stopka: `Wygenerowano przez apex_export_to_md | Autor: <author_name> | Współpraca z Claude (Anthropic)`
- Nazwa autora konfigurowalna opcją `--author-name`

---

## Architektura

### Pipeline przetwarzania

```
input_dir/
    f*.yaml          (definicja aplikacji)
    pages/
        p00001.yaml
        ...
    shared_components/
        ...
    *.sql              (pliki DDL — opcjonalnie)

         |
         v
  [find_app_root]   -- wykrywa katalog application/ rekursywnie
         |
         v
  ┌──────────────────────────────────────────────┐
  │            Pipeline APEX                      │
  │                                               │
  │  [parse_app_definition]  -- app name, ID      │
  │         |                                     │
  │  [parse_all_pages]       -- pages/p*.yaml     │
  │         |                                     │
  │  [PageFilter.filter_pages]  -- filtrowanie    │
  │         |                                     │
  │  [parse_shared_components]  -- LOV, auth...   │
  │         |                                     │
  │  [ApexApp]                                    │
  │       /   \                                   │
  │      v     v                                  │
  │ [HumanRenderer] [LLMRenderer]                 │
  │      |           |                            │
  │      v           v                            │
  │ *_human.md    *_llm.md                        │
  └──────────────────────────────────────────────┘
         |
         v  (jeśli znaleziono *.sql)
  ┌──────────────────────────────────────────────┐
  │            Pipeline DDL                       │
  │                                               │
  │  [find_sql_files]      -- szuka *.sql         │
  │         |                                     │
  │  [parse_ddl_files]     -- DDL/PL/SQL parser   │
  │         |                                     │
  │  [DbSchema]            -- tabele, widoki...   │
  │       /   \                                   │
  │      v     v                                  │
  │ [DbHumanRenderer] [DbLLMRenderer]             │
  │      |              |                         │
  │      v              v                         │
  │ *_db_human.md   *_db_llm.md                   │
  └──────────────────────────────────────────────┘
         |
         v  (jeśli DDL + APEX)
  ┌──────────────────────────────────────────────┐
  │            Pipeline HTML                      │
  │                                               │
  │  [ApexDbLinker]   -- heurystyki SQL           │
  │         |                                     │
  │  [HtmlRenderer]   -- vis.js, 3 zakładki       │
  │         |                                     │
  │         v                                     │
  │  *_interactive.html                           │
  └──────────────────────────────────────────────┘
```

### Moduły

| Moduł | Plik | Odpowiedzialność |
|-------|------|-----------------|
| `cli.py` | `apex_export_to_md/cli.py` | Parsowanie argumentów CLI, orkiestracja 3 pipeline'ów |
| `config.py` | `apex_export_to_md/config.py` | Dataclass `AppConfig`, stałe heurystyk |
| **Pipeline APEX** | | |
| `models/apex_models.py` | `models/` | Dataclassy: `ApexApp`, `ApexPage`, `Region`, `Column`, `Process` itp. — każda z polem `raw_attributes: dict` |
| `parser/page_parser.py` | `parser/` | Parsowanie `pages/p*.yaml` → `ApexPage` z pełnymi `raw_attributes` |
| `parser/shared_parser.py` | `parser/` | Parsowanie `shared_components/` → LOV, Auth, Nav itp. |
| `parser/yaml_helpers.py` | `parser/` | Pomocnicze funkcje YAML: `safe_get`, `strip_apex_id`, `collect_build_options`, `clean_raw_attributes()`, `_deep_clean()` |
| `filters/page_filter.py` | `filters/` | Klasa `PageFilter` — logika wszystkich trybów filtrowania |
| `renderers/base_renderer.py` | `renderers/` | ABC `BaseRenderer` — interfejs + helpery `_format_raw_yaml()`, `_format_raw_attributes()` |
| `renderers/human_renderer.py` | `renderers/` | Markdown z nagłówkami, tabelami, blokami kodu i `<details>` z pełnymi atrybutami |
| `renderers/llm_renderer.py` | `renderers/` | Format liniowy `PREFIX:wartość\|...` + linie `*_ATTRS:` z pełnymi atrybutami |
| **Pipeline DDL** | | |
| `models/db_models.py` | `models/` | Dataclassy schematu DB: `DbSchema`, `DbTable`, `DbColumn`, `DbConstraint`, `DbView`, `DbPackage`, `DbSequence` itp. |
| `parser/ddl_parser.py` | `parser/` | Parser DDL/PL/SQL: `parse_ddl_files()`, regex state machine, block splitter, package merge |
| `renderers/db_human_renderer.py` | `renderers/` | MD z diagramem Mermaid ER, tabelami kolumn/constraintów |
| `renderers/db_llm_renderer.py` | `renderers/` | Skondensowany format liniowy DB (`TBL:`, `COL:`, `PKG:` itp.) |
| **Pipeline HTML** | | |
| `linker/apex_db_linker.py` | `linker/` | `ApexDbLinker` — heurystyki SQL, word boundary matching |
| `renderers/html_renderer.py` | `renderers/` | Self-contained HTML z vis.js, 3 zakładki, branding, panele `raw_attributes` (JS: `renderRawAttrs` + `formatAttrsYaml`) |
| `renderers/vendor/vis-network.min.js` | `vendor/` | Bundled vis.js 9.1.6 (offline) |

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
# --- Pipeline APEX ---
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
# --- Pipeline DDL i HTML ---
enable_ddl: bool = True           # False = --no-ddl
ddl_files: list[str] = []         # jawne pliki SQL (--ddl-files)
enable_html: bool = True          # False = --no-html
html_output: str = ""             # jawna ścieżka HTML (--html-output)
author_name: str = "Tomasz Rembiasz"  # --author-name
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

1. Dodaj dataclass w `models/apex_models.py` — pamiętaj o polu `raw_attributes: dict = field(default_factory=dict)`
2. Dodaj logikę parsowania w `parser/page_parser.py` lub `parser/shared_parser.py` — wywołaj `clean_raw_attributes(data, skip_keys)` z odpowiednimi kluczami do pominięcia
3. Dodaj renderowanie w `renderers/human_renderer.py` (z `<details>` + YAML), `renderers/llm_renderer.py` (z linią `*_ATTRS:`) i `renderers/html_renderer.py` (z `renderRawAttrs()` w JS)

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
| **Pipeline APEX** | |
| `test_config.py` | `AppConfig` — wartości domyślne i pola |
| `test_models.py` | Dataclassy modelu APEX |
| `test_yaml_helpers.py` | Funkcje pomocnicze parsera YAML |
| `test_page_parser.py` | Parsowanie plików `pages/p*.yaml` |
| `test_shared_parser.py` | Parsowanie `shared_components/` |
| `test_page_filter.py` | Wszystkie tryby `PageFilter` |
| `test_human_renderer.py` | Format human Markdown |
| `test_llm_renderer.py` | Format LLM liniowy |
| `test_cli.py` | Parsowanie argumentów CLI |
| `test_integration.py` | Integracyjny end-to-end pipeline APEX |
| **Pipeline DDL** | |
| `test_db_models.py` | Dataclassy schematu DB (`DbSchema`, `DbTable` itp.) |
| `test_ddl_parser.py` | Parser DDL/PL/SQL: bloki, tabele, constrainty, widoki, pakiety, komentarze |
| `test_db_human_renderer.py` | Renderer DB human z diagramem Mermaid ER |
| `test_db_llm_renderer.py` | Renderer DB LLM (prefiksy `TBL:`, `PKG:` itp.) |
| **Pipeline HTML** | |
| `test_apex_db_linker.py` | Linker APEX↔DB: regiony, procesy, walidacje, LOV-y |
| `test_html_renderer.py` | HtmlRenderer: vis.js, 3 zakładki, branding, dane JSON |
| `test_cli_ddl.py` | Argumenty CLI dla DDL: `--no-ddl`, `--ddl-files`, `--no-html`, `--html-output`, `--author-name` |
| **Integracyjne** | |
| `test_integration_ddl.py` | Pełny pipeline DDL z prawdziwym `SKW_TO_APEX_DDL.sql` (8 testów) |

---

## Znane ograniczenia

1. **Tylko eksporty YAML readable** — narzędzie nie obsługuje starszego formatu SQL eksportu APEX (pliki `.sql`). Wymaga eksportu z opcją "Readable YAML".

2. **Brak obsługi Master Detail** — relacje parent/child między regionami (Master Detail) są parsowane jako flat lista regionów bez hierarchii.

3. **Częściowe parsowanie procesów API** — procesy typu "Invoke API" (np. wywołania REST) mają ograniczone parsowanie — wyciągany jest tylko typ i punkt wywołania, bez szczegółów parametrów.

4. **Brak parsowania Computations** — elementy APEX Computation (obliczenia wartości itemów) nie są aktualnie wyciągane.

5. **Brak parsowania Page Computations i Application Computations** — podobnie jak Computations na poziomie strony.

6. **LOV-y zagnieżdżone w kolumnach** — LOV przypisany bezpośrednio do kolumny Interactive Grid jest wyciągany tylko przez nazwę; jego definicja SQL nie jest inline rozwijana.

7. **Wewnętrzne ID APEX** — domyślnie są usuwane przez `strip_apex_id`. Opcja `--include-internal-ids` zachowuje je, ale nie jest jeszcze w pełni zaimplementowana we wszystkich parserach.

8. **Duże aplikacje** — przy aplikacjach z setkami stron i pełnym kodem (`--include-code full`) plik `*_human.md` może mieć kilka MB. Dla LLM zalecane jest `--include-code summary` lub `none`. Pełne atrybuty (`raw_attributes`) zwiększają rozmiar plików — format LLM może być większy niż Human z powodu dodatkowych linii `*_ATTRS:`.

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
