@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul 2>&1

echo [INFO] Sprawdzam czy port 8338 jest zajety...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8338" ^| findstr "LISTENING"') do (
    echo [INFO] Port 8338 zajety przez PID %%P - zamykam proces...
    taskkill /F /PID %%P >nul 2>&1
)

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [ERROR] Nie znaleziono wirtualnego srodowiska: ".venv\Scripts\activate.bat"
    echo [INFO] Utworz je poleceniem: python -m venv .venv
    popd
    exit /b 1
)

echo [INFO] Uruchamiam aplikacje w trybie GUI...
python -m apex_export_to_md --gui
set "EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %EXIT_CODE%
