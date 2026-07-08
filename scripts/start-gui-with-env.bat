@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

pushd "%REPO_ROOT%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Nie mozna przejsc do katalogu repozytorium: "%REPO_ROOT%"
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [ERROR] Nie znaleziono wirtualnego srodowiska: ".venv\Scripts\activate.bat"
    echo [INFO] Utworz je poleceniem: python -m venv .venv
    popd
    exit /b 1
)

if exist ".env" (
    for /f "usebackq delims=" %%L in (".env") do (
        set "line=%%L"
        if not "!line!"=="" if not "!line:~0,1!"=="#" (
            for /f "tokens=1* delims==" %%A in ("!line!") do (
                if not "%%A"=="" set "%%A=%%B"
            )
        )
    )
    echo [INFO] Zaladowano zmienne z pliku .env
) else (
    echo [WARN] Brak pliku .env - uruchamiam bez dodatkowych zmiennych srodowiskowych.
)

echo [INFO] Uruchamiam aplikacje w trybie GUI...
python -m apex_export_to_md --gui
set "EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %EXIT_CODE%
