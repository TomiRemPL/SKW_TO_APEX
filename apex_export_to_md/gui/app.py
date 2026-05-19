"""Serwer FastAPI — interfejs webowy do zarządzania eksportem APEX.

Uruchamiany przez: python -m apex_export_to_md --gui
Domyślny port: 8338 (nawiązanie do aliasu aplikacji START338)
"""
from __future__ import annotations
import logging
import threading
import webbrowser
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from apex_export_to_md.config import AppConfig
from apex_export_to_md.settings_manager import load_settings, save_settings

logger = logging.getLogger(__name__)

app = FastAPI(title="APEX Export to MD — GUI")

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Opisy parametrów po polsku (tooltipy)
PARAM_HELP: dict[str, str] = {
    "input_dir": "Ścieżka do katalogu eksportu APEX (zawiera pliki YAML i DDL)",
    "output_dir": "Katalog docelowy dla wygenerowanych plików",
    "output_prefix": "Prefiks nazw plików wyjściowych (np. apex_export)",
    "output_format": "Formaty wyjściowe: both (oba), human (czytelny Markdown), llm (zoptymalizowany dla AI)",
    "include_code": "Jak traktować bloki PL/SQL/JS: full (pełny kod), summary (skrót), none (pomiń)",
    "page_filter": "Filtr stron APEX: auto (heurystyki), all (wszystkie), prefix:X (po prefiksie), ids:1,2,3 (po ID)",
    "extra_pages": "Dodatkowe strony do dołączenia (ID rozdzielone przecinkami)",
    "include_internal_ids": "Zachowaj wewnętrzne identyfikatory APEX w eksporcie",
    "include_layout": "Zachowaj szczegóły layoutu stron (pozycja, template)",
    "include_shared_components": "Dołącz shared components (LOV, autoryzacje, menu, breadcrumbs)",
    "generate_ddl": "Generuje skrypt SQL tworzący obiekty bazy danych w nowym schemacie",
    "generate_migration": "Generuje pełny skrypt migracyjny z danymi (wymaga połączenia z bazą)",
    "db_connection": "Connection string Oracle, np. user@host:1521/service_name (hasło podaj osobno w polu poniżej)",
    "db_password": "Hasło do bazy danych (nie jest zapisywane w ustawieniach)",
    "verbose": "Włącz szczegółowe logi (poziom DEBUG)",
}


@app.get("/", response_class=HTMLResponse)
async def index():
    """Strona główna z formularzem."""
    html_path = TEMPLATES_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/settings")
async def get_settings():
    """Zwróć zapisane ustawienia."""
    settings = load_settings()
    return JSONResponse(content={"settings": settings, "help": PARAM_HELP})


@app.post("/api/settings")
async def post_settings(request: Request):
    """Zapisz ustawienia (bez hasła)."""
    data = await request.json()
    save_settings(data)
    return JSONResponse(content={"status": "ok", "message": "Ustawienia zapisane."})


@app.post("/api/test-connection")
async def post_test_connection(request: Request):
    """Testuj połączenie z bazą danych."""
    data = await request.json()
    conn_str = data.get("connection_string", "")
    if not conn_str:
        return JSONResponse(content={"success": False, "message": "Brak connection string."})
    try:
        from apex_export_to_md.db_exporter import test_connection
        success, message = test_connection(conn_str)
        return JSONResponse(content={"success": success, "message": message})
    except ImportError:
        return JSONResponse(content={
            "success": False,
            "message": "Pakiet 'oracledb' nie jest zainstalowany."
        })


@app.post("/api/run")
async def post_run(request: Request):
    """Uruchom pipeline z podanymi parametrami."""
    data = await request.json()
    try:
        config = _build_config_from_request(data)
        # Uruchom pipeline w osobnym wątku
        from apex_export_to_md.cli import run_pipeline
        import io
        import sys

        # Przechwytuj logi
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            run_pipeline(config)
            logs = log_capture.getvalue()
            return JSONResponse(content={
                "status": "ok",
                "message": "Pipeline zakończony pomyślnie.",
                "logs": logs,
            })
        except SystemExit:
            logs = log_capture.getvalue()
            return JSONResponse(content={
                "status": "error",
                "message": "Pipeline zakończył się błędem.",
                "logs": logs,
            })
        finally:
            root_logger.removeHandler(handler)
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"Błąd: {e}",
            "logs": "",
        })


def _build_config_from_request(data: dict[str, Any]) -> AppConfig:
    """Zbuduj AppConfig z danych żądania HTTP."""
    from apex_export_to_md.cli import find_app_root, _find_ddl_file
    from apex_export_to_md.parser.ddl_parser import parse_ddl_file

    input_dir = data.get("input_dir", "_data")
    input_path = Path(input_dir)

    # Wykryj plik DDL (szuka też w katalogach nadrzędnych)
    ddl_file = ""
    if input_path.exists():
        ddl_file = _find_ddl_file(input_path)

    # Buduj connection string z hasłem
    db_connection = data.get("db_connection", "")
    db_password = data.get("db_password", "")
    if db_password and db_connection and "/" not in db_connection.split("@")[0]:
        # Format: user@host:port/service → user/password@host:port/service
        if "@" in db_connection:
            user_part, host_part = db_connection.split("@", 1)
            db_connection = f"{user_part}/{db_password}@{host_part}"

    # Extra pages
    extra_pages: list[int] = []
    extra_str = data.get("extra_pages", "")
    if extra_str:
        for part in str(extra_str).split(","):
            part = part.strip()
            if part.isdigit():
                extra_pages.append(int(part))

    return AppConfig(
        input_dir=input_dir,
        output_dir=data.get("output_dir", "_out"),
        output_prefix=data.get("output_prefix", "apex_export"),
        output_format=data.get("output_format", "both"),
        include_code=data.get("include_code", "full"),
        page_filter=data.get("page_filter", "auto"),
        extra_pages=extra_pages,
        include_internal_ids=data.get("include_internal_ids", False),
        include_layout=data.get("include_layout", False),
        include_shared_components=data.get("include_shared_components", True),
        ddl_file=ddl_file,
        generate_ddl=data.get("generate_ddl", False),
        generate_migration=data.get("generate_migration", False),
        db_connection=db_connection,
        verbose=data.get("verbose", False),
    )


def start_gui(config: AppConfig) -> None:
    """Uruchom serwer GUI i otwórz przeglądarkę."""
    port = 8338
    url = f"http://localhost:{port}"

    # Otwórz przeglądarkę z opóźnieniem
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    logger.info("Uruchamiam GUI na %s", url)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
