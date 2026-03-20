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
from apex_export_to_md.parser.ddl_parser import parse_ddl_files
from apex_export_to_md.renderers.db_human_renderer import DbHumanRenderer
from apex_export_to_md.renderers.db_llm_renderer import DbLLMRenderer
from apex_export_to_md.linker.apex_db_linker import ApexDbLinker


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
    parser.add_argument(
        "--no-ddl", action="store_true",
        help="Pomiń pipeline SQL DDL",
    )
    parser.add_argument(
        "--ddl-files", default="",
        help="Pliki SQL do parsowania (rozdzielone przecinkami; domyślnie: auto)",
    )
    parser.add_argument(
        "--no-html", action="store_true",
        help="Pomiń generowanie interaktywnego HTML",
    )
    parser.add_argument(
        "--html-output", default="",
        help="Nazwa pliku HTML wyjściowego",
    )
    parser.add_argument(
        "--author-name", default="Tomasz Rembiasz",
        help="Autor w stopce HTML (domyślnie: Tomasz Rembiasz)",
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

    ddl_files_list: list[str] = []
    if args.ddl_files:
        ddl_files_list = [f.strip() for f in args.ddl_files.split(",") if f.strip()]

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
        enable_ddl=not args.no_ddl,
        ddl_files=ddl_files_list,
        enable_html=not args.no_html,
        html_output=args.html_output,
        author_name=args.author_name,
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

    # Fallback — zwróć podany katalog
    return input_dir


def find_sql_files(input_path: Path, config: AppConfig) -> list[Path]:
    """Znajdź pliki SQL w katalogu eksportu.

    Jeśli config.ddl_files podany — użyj wskazanych plików.
    W przeciwnym razie — auto-wykryj *.sql.
    """
    if config.ddl_files:
        return [Path(f) for f in config.ddl_files if Path(f).exists()]

    sql_files = list(input_path.rglob("*.sql"))
    if sql_files:
        logging.info("Znaleziono %d plików SQL: %s",
                     len(sql_files), [f.name for f in sql_files])
    return sql_files


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

    # 4. Parsuj shared components (jeśli włączone)
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

    # 6. Renderuj i zapisz pliki wyjściowe
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

    # --- Pipeline DDL ---
    sql_files = find_sql_files(input_path, config)
    schema = None

    if sql_files and config.enable_ddl:
        schema = parse_ddl_files(sql_files)
        logging.info("Sparsowano DDL: %d tabel, %d widoków, %d pakietów, %d sekwencji",
                     len(schema.tables), len(schema.views),
                     len(schema.packages), len(schema.sequences))

        if config.output_format in ("both", "human"):
            db_renderer = DbHumanRenderer(config)
            content = db_renderer.render(schema)
            out_path = output_dir / f"{config.output_prefix}_db_human.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

        if config.output_format in ("both", "llm"):
            db_renderer = DbLLMRenderer(config)
            content = db_renderer.render(schema)
            out_path = output_dir / f"{config.output_prefix}_db_llm.md"
            out_path.write_text(content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", out_path, len(content))

    # --- Pipeline HTML ---
    if schema and config.enable_html:
        linker = ApexDbLinker(app, schema)
        links = linker.find_links()
        logging.info("Znaleziono %d powiązań APEX↔DB", len(links))

        # Lazy import — HtmlRenderer może nie istnieć jeszcze (Task 11)
        try:
            from apex_export_to_md.renderers.html_renderer import HtmlRenderer
            html_renderer = HtmlRenderer(config)
            html_content = html_renderer.render(app, schema, links)
            html_name = config.html_output or f"{config.output_prefix}_interactive.html"
            html_path = output_dir / html_name
            html_path.write_text(html_content, encoding="utf-8")
            logging.info("Zapisano: %s (%d znaków)", html_path, len(html_content))
        except ImportError:
            logging.warning("HtmlRenderer niedostępny — pominięto generowanie HTML")


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

    run_pipeline(config)


if __name__ == "__main__":
    main()
