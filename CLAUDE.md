# CLAUDE.md

Ten plik zawiera wskazówki dla Claude Code (claude.ai/code) podczas pracy z tym repozytorium.
**Jezyk komunikacji: polski.**

## Opis projektu

Aplikacja Oracle APEX 24.1 dla **Systemu Kontroli Wewnetrznych i Audytu**. Baza Oracle, schemat `DAW`. UI po polsku. Aplikacja ID 141, alias START338141.

## Struktura repozytorium

```
SKW_TO_APEX/
├── CLAUDE.md                    # Ten plik — kontekst projektu
├── Wymagania.md                 # Dokument wymagan (PL) — czesc zrealizowana
├── program/
│   ├── skw_to_apex_DDL.sql      # Pelny DDL: tabele, widoki, sekwencje, pakiety PL/SQL
│   └── readable/application/    # Eksport APEX (YAML, app ID 141, alias START338141)
│       ├── f141.yaml            # Definicja aplikacji
│       ├── pages/               # 31 stron APEX (p00000–p20010)
│       └── shared_components/   # LOV, auth, nawigacja, role ACL
├── apex_export_to_md/           # Pipeline Python: YAML APEX → Markdown/HTML
│   ├── cli.py                   # CLI z argumentami
│   ├── config.py                # AppConfig, stale heurystyk
│   ├── parser/                  # Parser YAML stron + DDL (page_parser, ddl_parser, shared_parser, yaml_helpers)
│   ├── renderers/               # Human, LLM, HTML (vis.js), DB Human, DB LLM + vendor/
│   ├── linker/                  # Wykrywanie powiazan APEX↔DB (ApexDbLinker)
│   ├── models/                  # apex_models.py (z raw_attributes), db_models.py
│   └── filters/                 # Filtry stron (PageFilter)
├── tests/                       # 21 plikow pytest — 175 testow, 8 skipped
├── docs/superpowers/            # Plany i specyfikacje pipeline'u
├── requirements.txt             # PyYAML>=6.0, pytest>=7.0 (Python 3.10+)
└── apex_export_*.md/html        # Wygenerowane dokumentacje
```

## Wdrozenie

Brak CI/CD. Wdrozenie reczne:
1. Wykonaj `program/skw_to_apex_DDL.sql` na bazie Oracle (schemat `DAW`)
2. Import `program/` do Oracle APEX przez narzedzie importu lub CLI

## Architektura bazy danych

### Tabele (11)

| Tabela | Klucz | Opis |
|---|---|---|
| `B_AUDYT` | `ID_PK_B_AUDYT` (identity) | Audyty; cykl: `Otwarty` → `Zamrozony` → `Zakonczony` (CHECK constraint) |
| `B_KONTROLA` | `ID_PK_B_KONTROLA` (identity) | Definicje kontroli (zrodlo: SCOPE_DEFINITION Excel); klucz biznesowy: `REFERENCE_ID` |
| `B_KONTROLA_HIST` | `ID_PK_B_KONTROLA_HIST` (identity) | Historia zmian kontroli — archiwizacja starej wersji przy kazdej aktualizacji importem |
| `B_KONTROLA_IMPORT` | `ID` (identity) | Tabela stagingowa importu Excel; sesja: `ID_SESJI_IMPORTU`; statusy: `NOWY`/`OK`/`BLAD` |
| `B_KONTROLA_TMP` | `ID` (identity) | Tabela tymczasowa (do usuniecia) |
| `B_AUDYT_KONTROLA` | `ID_PK_B_AUDYT_KONTROLA` (identity) | Lacznik audyt↔kontrola; UNQ(`ID_FK_B_AUDYT`, `ID_FK_B_KONTROLA`) |
| `B_ANKIETA` | `ID_PK_B_ANKIETA` (seq) | Odpowiedzi ankiety: audyt+kontrola+pytanie |
| `B_OCENA` | `ID_PK_B_OCENA` (seq) | Oceny (wyliczone/nadpisane): audyt+kontrola+dziedzina |
| `B_IMPORT_LOG` | `ID_PK_B_IMPORT_LOG` (identity) | Logi importu ze statystykami (dodane/zmodyfikowane/dezaktywowane/bledy) |
| `B_SL_C_PYTANIE` | `ID_PK_B_SL_C_PYTANIE` (seq) | Slownik pytan ankiety |
| `B_SL_C_PYTANIE_DZIEDZINA` | `ID_PK_B_C_PYTANIE_DZIEDZINA` (seq) | Slownik dziedzin (np. Adekwatnosc=1, Skutecznosc=2) |

### Widoki (2)

- `B_V_AUDYT_KONTROLE` — Kontrole przypisane do audytow z full join (AUDYT_KONTROLA + KONTROLA + AUDYT)
- `B_V_IMPORT_STATYSTYKI` — Historia importow z podsumowaniem tekstowym

### Pakiety PL/SQL (3)

**`PKG_AUDYT`** — Cykl zycia audytu i uprawnienia:
- `UTWORZ_AUDYT(p_numer, p_uzytkownik, p_id OUT)` — Tworzy audyt (status=`Otwarty`, uzytkownik=szef misji)
- `DODAJ_KONTROLE / USUN_KONTROLE` — Dodaj/usun kontrole (tylko `Otwarty`, szef lub audytor)
- `ZAMROZ_AUDYT` — `Otwarty` → `Zamrozony` (tylko szef misji)
- `ZAKONCZ_AUDYT` — `Zamrozony` → `Zakonczony` (tylko szef misji)
- `SPRAWDZ_UPRAWNIENIA` → `'SZEF'` / `'AUDYTOR'` / `'BRAK'`
- `MOZE_EDYTOWAC` → BOOLEAN (szef/audytor AND nie `Zakonczony`)
- Kody bledow: `-20001` do `-20041`

**`PKG_IMPORT_KONTROLI`** — Miesieczny import kontroli z Excela:
- `WYKONAJ_IMPORT(p_id_sesji, p_nazwa_pliku, p_uzytkownik, p_id_log OUT)` — Glowna procedura
- `WALIDUJ_STAGING(p_id_sesji, p_id_log)` — Walidacja: brak REFERENCE_ID, duplikaty
- `CZY_ROZNE(a, b)` → BOOLEAN — NULL-safe porownanie VARCHAR2
- Logika importu: INSERT nowych → UPDATE zmienionych (z archiwizacja do `B_KONTROLA_HIST`) → DEACTIVATE nieobecnych → statystyki

**`PKG_ANKIETA`** — Ankiety i oceny:
- `GENERUJ_ANKIETE(p_id_audytu, p_id_kontrola)` — Idempotentna; generuje B_ANKIETA + B_OCENA
- `USUN_ANKIETE(p_id_audytu, p_id_kontrola)` — Usuwa oceny i ankiety (bez COMMIT)

### Relacje kluczowe

```
B_AUDYT 1──N B_AUDYT_KONTROLA N──1 B_KONTROLA
B_AUDYT 1──N B_ANKIETA N──1 B_KONTROLA
B_AUDYT 1──N B_OCENA   N──1 B_KONTROLA
B_KONTROLA 1──N B_KONTROLA_HIST (historia zmian)
B_IMPORT_LOG 1──N B_KONTROLA_IMPORT (staging)
B_SL_C_PYTANIE_DZIEDZINA 1──N B_SL_C_PYTANIE
```

## Bezpieczenstwo i autoryzacja

- **Autentykacja:** ADFS (Active Directory przez APEX)
- **Uzytkownik sesyjny:** `APP_USER`; porownywany z `SZEF_MISJI_LOGIN` i `AUDYTORZY_LOGINY` (CSV)
- **Autorizacja:** Role-based (ACL), uprawnienia na poziomie pol zalezne od czlonkostwa w zespole audytu
- **Inne:** Browser cache disabled, embed-in-frames denied, strict-origin referrer, html-escaping: Extended

## Grupy stron APEX

| Zakres | Przeznaczenie |
|---|---|
| `p00000`–`p00006` | Systemowe/logowanie |
| `p09999` | Globalna strona (zwykle puste) |
| `p10000`–`p10061` | Zarzadzanie audytami, kontrolami, import, ankiety |
| `p20000`–`p20010` | Funkcje dodatkowe |

Po filtracji auto (tryb domyslny): 7 stron — Home(1), DAW_ANKIETA(2), DAW_WYSZUKIWANIE(3), DAW_LISTA_AUDYTOW(4), DAW_IMPORT_KONTROLI(5), DAW_WYBOR_KONTROLI(6), Help(10061).

## Znane problemy / uwagi

- DDL (`skw_to_apex_DDL.sql`) zawiera **duplikaty** definicji tabel, indeksow i COMMENT (sekcje 1–319 i 320–855) — nalezy wyczyscic
- `B_KONTROLA_TMP` jest oznaczona do usuniecia w przyszlosci
- `requirements.txt` zalezy tylko od `PyYAML>=6.0` i `pytest>=7.0`

## Pipeline apex_export_to_md — pelne atrybuty APEX

### Mechanizm `raw_attributes`

Kazdy obiekt APEX (strona, region, kolumna, item, przycisk, proces, akcja dynamiczna, walidacja, branch) posiada pole `raw_attributes: dict` z **pelna** struktura YAML po usunieciu ID APEX i kluczy technicznych. Dzieki temu pliki wynikowe zawieraja komplet informacji o atrybutach/parametrach kazdego obiektu (np. appearance, layout, settings, security, session-state, help, configuration, dialog, attributes specyficzne dla typu regionu).

### Co przechowuja `raw_attributes`

Klucze wyekstrahowane jawnie do pol modelu (np. `name`, `type`, `source_table`, `code`) sa **wykluczone** z `raw_attributes`, unikajac duplikacji. Pozostale klucze YAML sa oczyszczane z ID APEX (np. `'Administration # 326184204701728798'` → `'Administration'`) i zachowywane w pelni.

### Renderowanie

- **Human** — sekcje `<details><summary>Pelne atrybuty ...</summary>` z blokiem YAML
- **LLM** — linie `*_ATTRS:` z forma splaszczona `klucz=wartosc;klucz.zagniezdzony=wartosc`
- **HTML** — rozwiniete panele YAML w zakladce APEX↔DB (funkcja JS `renderRawAttrs` + `formatAttrsYaml`)

### Pliki modyfikowane przy zmianie atrybutow

- `models/apex_models.py` — dodanie `raw_attributes` do dataclass
- `parser/yaml_helpers.py` — `clean_raw_attributes()` i `_deep_clean()`
- `parser/page_parser.py` — wywolanie `clean_raw_attributes()` w kazdym sub-parserze
- `renderers/base_renderer.py` — helpery `_format_raw_yaml()`, `_format_raw_attributes()`
- `renderers/human_renderer.py`, `llm_renderer.py`, `html_renderer.py` — renderowanie atrybutow

## Testy

- **21 plikow testowych**, **175 testow przechodzi**, 8 skipped (DDL integracyjne bez pliku SQL)
- Uruchomienie: `python -m pytest tests/ -v`
- Pipeline: `python -m apex_export_to_md program/readable/application/`
