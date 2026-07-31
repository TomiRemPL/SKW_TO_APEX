"""Raport pokrycia mapowania elementów APEX.

Weryfikuje kompletność parsowania: dla zdefiniowanej allow-listy "interesujących"
ścieżek kluczy YAML (w _data/readable/application/) sprawdza, czy odpowiadające
pola w modelach (załadowanych przez istniejące parsery) są wypełnione.

Użycie:
    python -m apex_export_to_md.coverage_report [input_dir] [--output ścieżka]
"""
from __future__ import annotations
import json
import logging
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import yaml

from apex_export_to_md.models import ApexApp
from apex_export_to_md.parser.yaml_helpers import sanitize_yaml_text

logger = logging.getLogger(__name__)


# --- Allow-lista "interesujących" kluczy YAML do weryfikacji pokrycia ---
# Format: (etykieta kategorii, ścieżka pliku względem application/, ścieżka klucza YAML)
# Każdy wpis to jeden element do policzenia: ile wystąpień w źródle vs. ile sparsowano.

PAGE_CHECKS: list[tuple[str, str]] = [
    ("region.server-side-condition", "server-side-condition"),
    ("region.appearance.template-options", "appearance.template-options"),
    ("region.attributes.pagination", "attributes.pagination"),
    ("region.layout.slot", "layout.slot"),
    ("region.layout.sequence", "layout.sequence"),
    ("region.source.location", "source.location"),
    ("column.layout.column-alignment", "layout.column-alignment"),
    ("column.heading.alignment", "heading.alignment"),
    ("column.enable-users-to.sort", "enable-users-to.sort"),
    ("page-item.session-state.data-type", "session-state.data-type"),
    ("page-item.session-state.storage", "session-state.storage"),
    ("page-item.security.session-state-protection", "security.session-state-protection"),
    ("page-item.security.store-value-encrypted", "security.store-value-encrypted-in-session-state"),
    ("page-item.layout.region", "layout.region"),
    ("process.error.display-location", "error.display-location"),
    ("computation.item-name", "identification.item-name"),
    ("page.dialog.chained", "dialog.chained"),
    ("page.help.help-text", "help.help-text"),
    ("page.appearance.template-options", "appearance.template-options"),
    ("page.javascript.function-and-global-variable-declaration",
     "javascript.function-and-global-variable-declaration"),
    ("page.server-cache.caching", "server-cache.caching"),
]

SHARED_FILES: list[tuple[str, str]] = [
    ("authentications", "shared_components/authentications.yaml"),
    ("plugins", "shared_components/plugins.yaml"),
    ("search_configs", "shared_components/search_configs.yaml"),
    ("data_load_defs", "shared_components/data_load_definitions.yaml"),
    ("static_files", "shared_components/app_static_files.yaml"),
    ("page_groups", "page_groups.yaml"),
]


def _safe_yaml_load(path: Path) -> Any:
    """Wczytaj YAML przez sanitize_yaml_text (wymóg dla plików z tabami)."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(sanitize_yaml_text(f.read()))
    except Exception as e:
        logger.warning("Błąd wczytywania %s: %s", path.name, e)
        return None


def _deep_get(data: Any, dotted: str) -> Any:
    """Bezpieczny odczyt zagnieżdżonej ścieżki z kropkami."""
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
        else:
            return None
        if cur is None:
            return None
    return cur


def _count_yaml_presence(pages_dir: Path) -> dict[str, dict]:
    """Policz wystąpienia kluczy z allow-listy w plikach stron."""
    totals: dict[str, dict] = {}
    for label, _ in PAGE_CHECKS:
        totals[label] = {"yaml_present": 0, "files": []}

    for yaml_file in sorted(pages_dir.glob("p*.yaml")):
        data = _safe_yaml_load(yaml_file)
        if not isinstance(data, dict):
            continue

        # Kontekst: regiony, kolumny, itemy, procesy, komputacje + poziom strony
        regions = data.get("regions", []) or []
        columns = [c for r in regions if isinstance(r, dict) for c in (r.get("columns") or [])]
        items = data.get("page-items", []) or []
        processes = data.get("processes", []) or []
        computations = data.get("computations") or []

        def _check(label: str, key_path: str, containers: list[Any]) -> None:
            for c in containers:
                if isinstance(c, dict) and _deep_get(c, key_path) is not None:
                    totals[label]["yaml_present"] += 1
                    totals[label]["files"].append(yaml_file.name)
                    break  # jeden plik liczymy raz per kategoria

        for label, key_path in PAGE_CHECKS:
            if label.startswith("region."):
                containers = regions
            elif label.startswith("column."):
                containers = columns
            elif label.startswith("page-item."):
                containers = items
            elif label.startswith("process."):
                containers = processes
            elif label.startswith("computation."):
                containers = computations
            elif label.startswith("page."):
                # Poziom całej strony
                if _deep_get(data, key_path) is not None:
                    totals[label]["yaml_present"] += 1
                    totals[label]["files"].append(yaml_file.name)
                continue
            else:
                continue
            _check(label, key_path, containers)

    return totals


def _model_field_populated(app: ApexApp) -> dict[str, int]:
    """Policz ile modeli ma wypełnione nowe pola (miara skuteczności parsera)."""
    counts: Counter = Counter()

    for page in app.pages:
        counts["page.server_cache"] += 1 if page.server_cache else 0
        counts["page.help_text"] += 1 if page.help_text else 0
        counts["page.page_template"] += 1 if page.page_template else 0
        counts["page.template_options"] += 1 if page.template_options else 0
        counts["page.javascript_full"] += 1 if page.javascript_full else 0
        counts["page.dialog"] += 1 if page.dialog else 0
        counts["page.computations"] += len(page.computations)

        for r in page.regions:
            counts["region.server_side_condition"] += 1 if r.server_side_condition else 0
            counts["region.template_options"] += 1 if r.template_options else 0
            counts["region.pagination"] += 1 if r.pagination else 0
            counts["region.slot"] += 1 if r.slot else 0
            counts["region.sequence"] += 1 if r.sequence else 0
            counts["region.source_location"] += 1 if r.source_location else 0
            for c in r.columns:
                counts["column.column_alignment"] += 1 if c.column_alignment else 0
                counts["column.heading_alignment"] += 1 if c.heading_alignment else 0
                counts["column.sortable"] += 1 if c.sortable else 0
        for it in page.items:
            counts["page_item.data_type"] += 1 if it.data_type else 0
            counts["page_item.storage"] += 1 if it.storage else 0
            counts["page_item.session_state_protection"] += 1 if it.session_state_protection else 0
            counts["page_item.store_encrypted"] += 1 if it.store_encrypted else 0
            counts["page_item.region"] += 1 if it.region else 0
        for p in page.processes:
            counts["process.error_display_location"] += 1 if p.error_display_location else 0

    # Shared components
    counts["shared.authentications"] = len(app.authentications)
    counts["shared.plugins"] = len(app.plugins)
    counts["shared.search_configs"] = len(app.search_configs)
    counts["shared.data_load_defs"] = len(app.data_load_defs)
    counts["shared.static_files"] = len(app.static_files)
    counts["shared.page_groups"] = len(app.page_groups)

    return dict(counts)


# Mapowanie: kategoria YAML → odpowiadające pole modelu (do % pokrycia)
YAML_TO_MODEL: dict[str, str] = {
    "region.server-side-condition": "region.server_side_condition",
    "region.appearance.template-options": "region.template_options",
    "region.attributes.pagination": "region.pagination",
    "region.layout.slot": "region.slot",
    "region.layout.sequence": "region.sequence",
    "region.source.location": "region.source_location",
    "column.layout.column-alignment": "column.column_alignment",
    "column.heading.alignment": "column.heading_alignment",
    "column.enable-users-to.sort": "column.sortable",
    "page-item.session-state.data-type": "page_item.data_type",
    "page-item.session-state.storage": "page_item.storage",
    "page-item.security.session-state-protection": "page_item.session_state_protection",
    "page-item.security.store-value-encrypted": "page_item.store_encrypted",
    "page-item.layout.region": "page_item.region",
    "process.error.display-location": "process.error_display_location",
    "computation.item-name": "page.computations",
    "page.dialog.chained": "page.dialog",
    "page.help.help-text": "page.help_text",
    "page.appearance.template-options": "page.template_options",
    "page.javascript.function-and-global-variable-declaration": "page.javascript_full",
    "page.server-cache.caching": "page.server_cache",
}


def generate_coverage_report(input_dir: str = "_data") -> dict:
    """Wygeneruj raport pokrycia mapowania.

    Args:
        input_dir: Katalog eksportu APEX (z readable/application/ w środku)

    Returns:
        Słownik ze statystykami: per-kategoria yaml_present/model_filled/coverage_pct
        oraz podsumowanie shared files.
    """
    from apex_export_to_md.cli import find_app_root
    from apex_export_to_md.parser.page_parser import parse_all_pages
    from apex_export_to_md.parser.shared_parser import parse_shared_components

    app_root = find_app_root(Path(input_dir))
    pages_dir = app_root / "pages"
    shared_dir = app_root / "shared_components"

    # 1. Policz wystąpienia kluczy YAML w plikach źródłowych
    yaml_presence = _count_yaml_presence(pages_dir)

    # 2. Załaduj modele przez istniejące parsery
    pages = parse_all_pages(pages_dir)
    shared = parse_shared_components(shared_dir)
    app = ApexApp(
        name="coverage", id="?", pages=pages, **shared,
    )
    model_counts = _model_field_populated(app)

    # 3. Zbuduj per-kategoria statystyki pokrycia
    categories: list[dict] = []
    for yaml_label, model_field in YAML_TO_MODEL.items():
        yaml_count = yaml_presence.get(yaml_label, {}).get("yaml_present", 0)
        model_count = model_counts.get(model_field, 0)
        # coverage: model nie może być > źródła, ale liczby liczone są różnie
        # (yaml_present = liczba plików; model_count = liczba elementów).
        # Dla kategorii "per-element" liczymy po prostu: czy model > 0 gdy yaml > 0.
        if yaml_count == 0:
            pct = 100.0  # brak źródła = pełne pokrycie (nie ma czego mapować)
        else:
            pct = round(min(100.0, (model_count / max(yaml_count, 1)) * 100), 1)
            # Korekta: jeśli model ma więcej elementów niż plików (bo wiele per strona),
            # traktujemy jako pełne pokrycie, gdy model_count > 0.
            if model_count >= yaml_count:
                pct = 100.0
        categories.append({
            "category": yaml_label,
            "model_field": model_field,
            "yaml_present": yaml_count,
            "model_filled": model_count,
            "coverage_pct": pct,
        })

    # 4. Shared files presence
    shared_status: list[dict] = []
    for label, rel_path in SHARED_FILES:
        full = app_root / rel_path
        data = _safe_yaml_load(full)
        count = len(app.authentications) if label == "authentications" else \
                len(app.plugins) if label == "plugins" else \
                len(app.search_configs) if label == "search_configs" else \
                len(app.data_load_defs) if label == "data_load_defs" else \
                len(app.static_files) if label == "static_files" else \
                len(app.page_groups)
        shared_status.append({
            "component": label,
            "file": rel_path,
            "file_exists": full.exists(),
            "yaml_entries": len(data) if isinstance(data, list) else (1 if data else 0),
            "model_entries": count,
            "mapped": count > 0,
        })

    # 5. Podsumowanie
    mapped_cats = sum(1 for c in categories if c["yaml_present"] > 0 and c["model_filled"] > 0)
    source_cats = sum(1 for c in categories if c["yaml_present"] > 0)
    overall_pct = round((mapped_cats / source_cats * 100), 1) if source_cats else 100.0
    mapped_shared = sum(1 for s in shared_status if s["mapped"])
    source_shared = sum(1 for s in shared_status if s["file_exists"])

    return {
        "input_dir": str(app_root),
        "pages_count": len(pages),
        "overall_coverage_pct": overall_pct,
        "categories_mapped": f"{mapped_cats}/{source_cats}",
        "shared_mapped": f"{mapped_shared}/{source_shared}",
        "categories": categories,
        "shared_components": shared_status,
    }


def format_report_text(report: dict) -> str:
    """Sformatuj raport jako czytelny tekst."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("RAPORT POKRYCIA MAPOWANIA ELEMENTÓW APEX")
    lines.append("=" * 70)
    lines.append(f"Katalog: {report['input_dir']}")
    lines.append(f"Strony: {report['pages_count']}")
    lines.append(f"Pokrycie ogólne: {report['overall_coverage_pct']}% "
                 f"({report['categories_mapped']} kategorii)")
    lines.append(f"Shared components: {report['shared_mapped']} plików")
    lines.append("")
    lines.append("--- KATEGORIE (strony) ---")
    lines.append(f"{'Kategoria':<55} {'YAML':>6} {'Model':>6} {'%':>6}")
    lines.append("-" * 75)
    for c in sorted(report["categories"], key=lambda x: x["coverage_pct"]):
        lines.append(f"{c['category']:<55} {c['yaml_present']:>6} "
                     f"{c['model_filled']:>6} {c['coverage_pct']:>5}%")
    lines.append("")
    lines.append("--- SHARED COMPONENTS ---")
    lines.append(f"{'Komponent':<20} {'Plik':<45} {'Mapowane':>9}")
    lines.append("-" * 75)
    for s in report["shared_components"]:
        flag = "TAK" if s["mapped"] else ("BRAK" if s["file_exists"] else "—")
        lines.append(f"{s['component']:<20} {s['file']:<45} {flag:>9}")
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def run_coverage(input_dir: str = "_data", output_dir: str = "_out",
                 as_json: bool = False) -> str:
    """Uruchom raport pokrycia i zapisz wynik.

    Returns:
        Ścieżka do zapisanego pliku raportu.
    """
    report = generate_coverage_report(input_dir)

    out_path_dir = Path(output_dir)
    out_path_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".json" if as_json else ".txt"
    out_path = out_path_dir / f"coverage_report{suffix}"

    if as_json:
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        out_path.write_text(format_report_text(report), encoding="utf-8")

    logging.info("Zapisano raport pokrycia: %s", out_path)
    return str(out_path)


def main() -> None:
    """Punkt wejścia: python -m apex_export_to_md.coverage_report [input] [--json]."""
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(prog="apex_export_to_md.coverage_report",
                                     description="Raport pokrycia mapowania elementów APEX.")
    parser.add_argument("input_dir", nargs="?", default="_data")
    parser.add_argument("--output-dir", default="_out")
    parser.add_argument("--json", action="store_true", help="Wyjście JSON zamiast tekstu")
    args = parser.parse_args()
    path = run_coverage(args.input_dir, args.output_dir, as_json=args.json)
    print(f"Raport pokrycia zapisany: {path}")
    # Wydrukuj podsumowanie na konsolę
    report = generate_coverage_report(args.input_dir)
    print(format_report_text(report))


if __name__ == "__main__":
    main()
