"""Punkt wejścia CLI — parsowanie argumentów i orkiestracja pipeline'u.

Użycie:
    python -m apex_export_to_md [ścieżka_do_exportu] [opcje]
"""
from __future__ import annotations
import argparse
from datetime import datetime
import logging
import sys
from pathlib import Path

from apex_export_to_md.config import AppConfig
from apex_export_to_md.app_logger import setup_file_logging
from apex_export_to_md.models import ApexApp
from apex_export_to_md.parser.page_parser import parse_all_pages
from apex_export_to_md.parser.shared_parser import (
    load_yaml_file, parse_app_definition, parse_shared_components,
)
from apex_export_to_md.parser.ddl_parser import parse_ddl_file
from apex_export_to_md.parser.app_sql_parser import parse_app_sql_file, find_app_sql_file
from apex_export_to_md.filters.page_filter import PageFilter
from apex_export_to_md.renderers.human_renderer import HumanRenderer
from apex_export_to_md.renderers.llm_renderer import LLMRenderer
from apex_export_to_md.renderers.ddl_human_renderer import DDLHumanRenderer
from apex_export_to_md.renderers.ddl_llm_renderer import DDLLLMRenderer
from apex_export_to_md.renderers.html_renderer import HTMLRenderer
from apex_export_to_md.renderers.ddl_script_renderer import DDLScriptRenderer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parsuj argumenty wiersza poleceń."""
    parser = argparse.ArgumentParser(
        prog="apex_export_to_md",
        description="Konwertuje eksport Oracle APEX (readable YAML) na Markdown.",
    )
    parser.add_argument(
        "input_dir", nargs="?", default="_data",
        help="Ścieżka do katalogu eksportu APEX (domyślnie: _data)",
    )
    parser.add_argument(
        "--output-dir", default="_out",
        help="Katalog wyjściowy (domyślnie: _out)",
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
        "--generate-ddl", action="store_true",
        help="Generuj skrypt SQL tworzący obiekty bazy danych w nowym schemacie",
    )
    parser.add_argument(
        "--generate-migration", action="store_true",
        help="Generuj pełny skrypt migracyjny z danymi (wymaga --db-connection)",
    )
    parser.add_argument(
        "--db-connection", default="",
        help="Connection string Oracle, np. user/pass@host:1521/service_name",
    )
    parser.add_argument(
        "--fetch-ddl-from-db", action="store_true",
        help="Pobierz DDL automatycznie z bazy Oracle na podstawie keyword w komentarzach",
    )
    parser.add_argument(
        "--ddl-keyword", default="",
        help="Keyword do filtrowania obiektów DB (np. */OnSite*/)",
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="Uruchom interfejs webowy (FastAPI) w przeglądarce",
    )
    parser.add_argument(
        "--coverage", action="store_true",
        help="Wygeneruj tylko raport pokrycia mapowania (bez pełnych plików)",
    )
    parser.add_argument(
        "--coverage-config", default="",
        help="Ścieżka do niestandardowego pliku reguł pokrycia YAML",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Szczegółowe logi",
    )
    return parser.parse_args(argv)


def args_to_config(args: argparse.Namespace) -> AppConfig:
    """Konwertuj argumenty CLI na obiekt konfiguracji."""
    # Przetwórz listę dodatkowych stron (string → lista int)
    extra_pages: list[int] = []
    if args.extra_pages:
        for part in args.extra_pages.split(","):
            part = part.strip()
            if part.isdigit():
                extra_pages.append(int(part))

    # Wykryj plik DDL w katalogu wejściowym (szuka też w katalogach nadrzędnych)
    ddl_file = ""
    input_path = Path(args.input_dir)
    if input_path.exists():
        ddl_file = _find_ddl_file(input_path)

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
        ddl_file=ddl_file,
        generate_ddl=args.generate_ddl,
        generate_migration=args.generate_migration,
        db_connection=args.db_connection,
        fetch_ddl_from_db=args.fetch_ddl_from_db,
        ddl_keyword=args.ddl_keyword,
        gui=args.gui,
        coverage=args.coverage,
        coverage_config=args.coverage_config,
        verbose=args.verbose,
    )


def _find_ddl_file(input_path: Path) -> str:
    """Znajdź plik DDL w katalogu wejściowym lub jego przodkach.

    Szuka plików *DDL*.sql najpierw w podanym katalogu,
    a następnie w katalogach nadrzędnych (max 3 poziomy w górę).
    """
    # Szukaj w podanym katalogu
    for f in input_path.iterdir():
        if f.is_file() and "DDL" in f.name.upper() and f.suffix.lower() == ".sql":
            return str(f)
    # Szukaj w katalogach nadrzędnych (np. gdy podano _data/readable/application/)
    parent = input_path.parent
    for _ in range(3):
        if parent == parent.parent:
            break
        for f in parent.iterdir():
            if f.is_file() and "DDL" in f.name.upper() and f.suffix.lower() == ".sql":
                return str(f)
        parent = parent.parent
    return ""


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

    # Fallback — zwróć podany katalog
    return input_dir


def run_pipeline(config: AppConfig) -> None:
    """Uruchom pełny pipeline: parse → filter → render → zapis."""
    input_path = Path(config.input_dir)
    if not input_path.exists():
        logging.error("Katalog nie istnieje: %s", input_path)
        sys.exit(1)

    # 0. Automatyczne pobieranie DDL z bazy (jeśli włączone)
    if config.fetch_ddl_from_db:
        from apex_export_to_md.ddl_fetcher import fetch_ddl_from_database

        # Walidacja
        if not config.db_connection:
            logging.error("Automatyczne pobieranie DDL wymaga --db-connection")
            sys.exit(1)
        if not config.ddl_keyword:
            logging.error("Automatyczne pobieranie DDL wymaga --ddl-keyword")
            sys.exit(1)

        logging.info("=== POBIERANIE DDL Z BAZY ORACLE ===")
        logging.info("Keyword: %s", config.ddl_keyword)

        # Pobierz DDL z bazy
        success, ddl_file_path = fetch_ddl_from_database(
            config.db_connection,
            config.ddl_keyword,
            input_path,
        )

        if not success:
            logging.error("Nie udało się pobrać DDL z bazy")
            sys.exit(1)

        # Ustaw ścieżkę do wygenerowanego pliku DDL
        config.ddl_file = ddl_file_path
        logging.info("Plik DDL zostanie użyty w pipeline: %s", config.ddl_file)
        logging.info("=" * 40)

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

    # 4. Parsuj shared components (jeśli włączone)
    shared = {}
    if config.include_shared_components:
        shared = parse_shared_components(shared_dir)

    # 5. Parsuj plik DDL (jeśli wykryty)
    ddl_schema = None
    if config.ddl_file:
        ddl_path = Path(config.ddl_file)
        if ddl_path.exists():
            ddl_schema = parse_ddl_file(ddl_path)

    # 5b. Parsuj plik f*.sql (metadane aplikacji)
    app_metadata = None
    app_sql_path = find_app_sql_file(input_path)
    if app_sql_path:
        app_metadata = parse_app_sql_file(app_sql_path)

    # 6. Zbuduj model aplikacji
    app = ApexApp(
        name=app_name or "APEX App",
        id=app_id or "?",
        alias=app_alias or "?",
        pages=filtered_pages,
        ddl_schema=ddl_schema,
        metadata=app_metadata,
        **shared,
    )

    # 7. Renderuj i zapisz pliki wyjściowe (z timestampem w nazwie)
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = config.output_prefix

    # Pliki APEX (human + LLM)
    if config.output_format in ("both", "human"):
        renderer = HumanRenderer(config)
        content = renderer.render(app)
        out_path = output_dir / f"{timestamp}_{prefix}_human.md"
        out_path.write_text(content, encoding="utf-8")
        logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    if config.output_format in ("both", "llm"):
        renderer = LLMRenderer(config)
        content = renderer.render(app)
        out_path = output_dir / f"{timestamp}_{prefix}_llm.md"
        out_path.write_text(content, encoding="utf-8")
        logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    # Pliki DDL (human + LLM) — tylko gdy wykryto plik DDL
    if ddl_schema:
        if config.output_format in ("both", "human"):
            renderer = DDLHumanRenderer(config)
            content = renderer.render(app)
            out_path = output_dir / f"{timestamp}_{prefix}_ddl_human.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

        if config.output_format in ("both", "llm"):
            renderer = DDLLLMRenderer(config)
            content = renderer.render(app)
            out_path = output_dir / f"{timestamp}_{prefix}_ddl_llm.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    # Plik HTML — interaktywna dokumentacja
    html_renderer = HTMLRenderer(config)
    html_content = html_renderer.render(app)
    html_path = output_dir / f"{timestamp}_{prefix}_dokumentacja.html"
    html_path.write_text(html_content, encoding="utf-8")
    logging.info("Zapisano: %s (%d znaków)", html_path, len(html_content))

    # Skrypt DDL (--generate-ddl)
    if config.generate_ddl and ddl_schema:
        ddl_renderer = DDLScriptRenderer(config)
        ddl_content = ddl_renderer.render(app)
        ddl_path = output_dir / f"{timestamp}_{prefix}_migration_ddl.sql"
        ddl_path.write_text(ddl_content, encoding="utf-8")
        logging.info("Zapisano DDL: %s (%d znaków)", ddl_path, len(ddl_content))

        # Skrypt rollback (wycofanie)
        from apex_export_to_md.renderers.rollback_renderer import RollbackRenderer
        rollback_renderer = RollbackRenderer(config)
        rollback_content = rollback_renderer.render(app)
        rollback_path = output_dir / f"{timestamp}_{prefix}_rollback.sql"
        rollback_path.write_text(rollback_content, encoding="utf-8")
        logging.info("Zapisano rollback: %s (%d znaków)", rollback_path, len(rollback_content))

    # Pełna migracja (--generate-migration)
    if config.generate_migration and ddl_schema:
        if not config.db_connection:
            logging.error("--generate-migration wymaga --db-connection")
            sys.exit(1)
        from apex_export_to_md.renderers.migration_renderer import MigrationRenderer
        from apex_export_to_md.db_exporter import export_all_data
        # Diagnostyka connection string (zamaskowane hasło)
        _masked = config.db_connection
        if "/" in _masked and "@" in _masked:
            _u, _rest = _masked.split("/", 1)
            _masked = f"{_u}/***@{_rest.split('@', 1)[1]}" if "@" in _rest else _masked
        logging.info("Łączenie z bazą: %s", _masked)
        db_data = export_all_data(config.db_connection, ddl_schema)

        # Podsumowanie wyeksportowanych danych
        total_rows = 0
        logging.info("")
        logging.info("=== PODSUMOWANIE EKSPORTU DANYCH ===")
        for td in db_data.tables:
            row_count = len(td.rows)
            total_rows += row_count
            logging.info("  Tabela %-40s: %d wierszy", td.table_name, row_count)
        logging.info("  %-40s  %s", "-" * 40, "-" * 10)
        logging.info("  %-40s: %d wierszy", "RAZEM", total_rows)
        logging.info("  Sekwencje wyeksportowane: %d", len(db_data.sequences))
        logging.info("  Kolumny identity: %d", len(db_data.identity_max_values))
        logging.info("")

        migration_renderer = MigrationRenderer(config, db_data)
        migration_content = migration_renderer.render(app)
        migration_path = output_dir / f"{timestamp}_{prefix}_migration_full.sql"
        migration_path.write_text(migration_content, encoding="utf-8")
        logging.info("Zapisano migrację: %s (%d znaków)", migration_path, len(migration_content))


def main() -> None:
    """Główna funkcja CLI."""
    args = parse_args()
    config = args_to_config(args)

    # Konfiguracja logowania — verbose włącza poziom DEBUG
    log_level = logging.DEBUG if config.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    # Logowanie do pliku (append mode)
    setup_file_logging(config.output_dir)

    # Tryb GUI
    if config.gui:
        from apex_export_to_md.gui.app import start_gui
        start_gui(config)
        return

    # Tryb raportu pokrycia (bez pełnego pipeline'u)
    if config.coverage:
        from apex_export_to_md.coverage_report import run_coverage
        run_coverage(config.input_dir, config.output_dir, coverage_config=config.coverage_config)
        return

    run_pipeline(config)


if __name__ == "__main__":
    main()
