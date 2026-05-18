# Copilot MCP — konfiguracja projektu

## Co jest skonfigurowane

W repo znajdują się serwery MCP w `\.vscode\mcp.json`:

- `fetch` — pobieranie treści z URL
- `selvedge` — śledzenie uzasadnień zmian

W `\.vscode\settings.json` dane połączenia SQLTools używają zmiennych środowiskowych (bez haseł w repo):

- `SKW_SQLTOOLS_USERNAME`
- `SKW_SQLTOOLS_PASSWORD`

## Szybkie uruchomienie (Windows)

1. Uzupełnij lokalnie plik `.env` (na bazie `.env.example`).
2. Ustaw zmienne w bieżącej sesji PowerShell:
   - `$env:SKW_SQLTOOLS_USERNAME = "..."`
   - `$env:SKW_SQLTOOLS_PASSWORD = "..."`
   - `$env:HTTPS_PROXY = "..."`
   - `$env:HTTP_PROXY = "..."`
3. Uruchom VS Code z tej samej sesji (żeby dziedziczył zmienne):
   - `code .`
4. W VS Code sprawdź panel MCP/Tools i upewnij się, że serwery `fetch` oraz `selvedge` są aktywne.

## Ważne

- `.env` jest ignorowany przez Git.
- `.env.example` jest wersjonowany jako szablon.
- Jeśli uruchamiasz VS Code spoza terminala, ustaw zmienne jako użytkownika/systemowe w Windows, aby `${env:...}` było widoczne dla edytora.

## Skrót: automatyczny start VS Code z `.env`

Dodany jest skrypt: `scripts/start-vscode-with-env.ps1`.
Dodatkowo jest wersja `cmd`: `scripts/start-vscode-with-env.cmd`.

Co robi:

1. Wczytuje pary `KEY=VALUE` z pliku `.env` (pomija komentarze i puste linie).
2. Ustawia je w bieżącym procesie PowerShell.
3. Korzysta ze standardowych zmiennych proxy:
   - `HTTPS_PROXY`
   - `HTTP_PROXY`
4. Dopina do `PATH` katalog `LOCAL_BIN` (z fallbackiem do `SKW_LOCAL_BIN`).
5. Uruchamia `code .` w katalogu repo.

W `.env` możesz ustawić własne wartości:

- `HTTPS_PROXY`
- `HTTP_PROXY`
- `LOCAL_BIN`

Przykład użycia (PowerShell):

- `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`
- `./scripts/start-vscode-with-env.ps1`

Przykład użycia (cmd):

- `scripts\start-vscode-with-env.cmd`
<!-- EOF -->