"""Raport pokrycia mapowania elementów APEX.

Weryfikuje kompletność parsowania: na podstawie reguł (z pliku coverage_rules.yaml)
sprawdza obecność kluczy YAML w źródle vs. wypełnienie pól w modelach,
oraz dynamicznie wykrywa nowe / niezmapowane klucze APEX z nowszych wersji eksportu.

Użycie:
    python -m apex_export_to_md.coverage_report [input_dir] [--coverage-config path]
"""
from __future__ import annotations
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from apex_export_to_md.models import ApexApp
from apex_export_to_md.parser.yaml_helpers import sanitize_yaml_text

logger = logging.getLogger(__name__)


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
    if not dotted:
        return data
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


def load_coverage_rules(custom_path: str | None = None, input_dir: str = "_data") -> dict:
    """Wczytaj reguły pokrycia mapowania APEX z plików YAML.

    Kolejność priorytetu:
    1. Wbudowane reguły domyślne: apex_export_to_md/config/coverage_rules.yaml
    2. Reguły projektu: <input_dir>/coverage_rules.yaml lub _data/coverage_rules.yaml
    3. Dedykowany plik podany w CLI (custom_path)
    """
    builtin_path = Path(__file__).parent / "config" / "coverage_rules.yaml"
    rules: dict[str, Any] = {
        "mapped_keys": {},
        "ignore_keys": [],
        "shared_files": {},
    }

    def _merge_rules(source: dict) -> None:
        if not isinstance(source, dict):
            return
        if "mapped_keys" in source and isinstance(source["mapped_keys"], dict):
            rules["mapped_keys"].update(source["mapped_keys"])
        if "ignore_keys" in source and isinstance(source["ignore_keys"], list):
            for item in source["ignore_keys"]:
                if item not in rules["ignore_keys"]:
                    rules["ignore_keys"].append(item)
        if "shared_files" in source and isinstance(source["shared_files"], dict):
            rules["shared_files"].update(source["shared_files"])

    if builtin_path.exists():
        data = _safe_yaml_load(builtin_path)
        if data:
            _merge_rules(data)

    # Domyślny szum metadanych APEX (podstawowa struktura identyfikacyjna)
    default_noise = [
        "identification", "sequence", "id", "name", "alias",
        "type", "title", "prompt", "slot", "display-sequence",
    ]
    for noise in default_noise:
        if noise not in rules["ignore_keys"]:
            rules["ignore_keys"].append(noise)

    input_p = Path(input_dir)
    candidates = [
        input_p / "coverage_rules.yaml",
        input_p.parent / "coverage_rules.yaml",
        Path("_data") / "coverage_rules.yaml",
    ]
    try:
        from apex_export_to_md.cli import find_app_root
        app_root = find_app_root(input_p)
        candidates.append(app_root / "coverage_rules.yaml")
    except Exception:
        pass

    loaded_paths = {builtin_path.resolve()} if builtin_path.exists() else set()
    for cand in candidates:
        if cand.exists():
            cand_res = cand.resolve()
            if cand_res not in loaded_paths:
                data = _safe_yaml_load(cand)
                if data:
                    _merge_rules(data)
                loaded_paths.add(cand_res)

    if custom_path:
        custom_p = Path(custom_path)
        if custom_p.exists():
            cand_res = custom_p.resolve()
            if cand_res not in loaded_paths:
                data = _safe_yaml_load(custom_p)
                if data:
                    _merge_rules(data)
                loaded_paths.add(cand_res)
        else:
            logger.warning("Plik reguł podany w CLI nie istnieje: %s", custom_path)

    return rules


def _extract_paths(val: Any, prefix: str, skip_containers: set[str] | None = None) -> set[str]:
    """Rekurencyjnie wyciągnij ścieżki kropkowe kluczy z obiektu dict."""
    if skip_containers is None:
        skip_containers = set()
    paths: set[str] = set()

    if isinstance(val, dict):
        for k, v in val.items():
            if v is None or k in skip_containers:
                continue
            curr_path = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                sub_paths = _extract_paths(v, curr_path, skip_containers)
                if sub_paths:
                    paths.update(sub_paths)
                else:
                    paths.add(curr_path)
            elif isinstance(v, list):
                if not v:
                    continue
                has_dict = False
                for item in v:
                    if isinstance(item, dict):
                        has_dict = True
                        paths.update(_extract_paths(item, curr_path, skip_containers))
                if not has_dict:
                    paths.add(curr_path)
            else:
                paths.add(curr_path)
    return paths


def crawl_unmapped_keys(pages_dir: Path, rules: dict) -> list[dict]:
    """Przeszukaj pliki YAML stron i znajdź niezmapowane / nowe klucze APEX."""
    mapped_keys = rules.get("mapped_keys", {})
    ignore_keys = rules.get("ignore_keys", [])

    key_counts: Counter = Counter()
    key_files: dict[str, list[str]] = {}

    def _is_mapped(path: str) -> bool:
        if path in mapped_keys:
            return True
        for mk in mapped_keys:
            if path.startswith(mk + "."):
                return True
        return False

    def _is_ignored(path: str) -> bool:
        parts = path.split(".")
        for ign in ignore_keys:
            if ign in parts:
                return True
            if "." in ign and ign in path:
                return True
            if path == ign or path.endswith("." + ign) or path.startswith(ign + "."):
                return True
        return False

    if not pages_dir.exists():
        return []

    for yaml_file in sorted(pages_dir.glob("p*.yaml")):
        data = _safe_yaml_load(yaml_file)
        if not isinstance(data, dict):
            continue

        file_paths: set[str] = set()

        file_paths.update(_extract_paths(
            data, prefix="page",
            skip_containers={"regions", "page-items", "items", "processes", "computations",
                             "dynamic-actions", "buttons", "branches", "validations",
                             "header", "footer"}
        ))

        for r in data.get("regions") or []:
            if isinstance(r, dict):
                file_paths.update(_extract_paths(
                    r, prefix="region",
                    skip_containers={"columns", "report-columns", "buttons", "page-items", "items"}
                ))
                for c in (r.get("columns") or []) + (r.get("report-columns") or []):
                    if isinstance(c, dict):
                        file_paths.update(_extract_paths(c, prefix="column"))

        for item in (data.get("page-items") or []) + (data.get("items") or []):
            if isinstance(item, dict):
                file_paths.update(_extract_paths(item, prefix="page-item"))

        for proc in data.get("processes") or []:
            if isinstance(proc, dict):
                file_paths.update(_extract_paths(proc, prefix="process"))

        for comp in data.get("computations") or []:
            if isinstance(comp, dict):
                file_paths.update(_extract_paths(comp, prefix="computation"))

        for da in data.get("dynamic-actions") or []:
            if isinstance(da, dict):
                file_paths.update(_extract_paths(da, prefix="dynamic-action"))

        for btn in data.get("buttons") or []:
            if isinstance(btn, dict):
                file_paths.update(_extract_paths(btn, prefix="button"))

        for br in data.get("branches") or []:
            if isinstance(br, dict):
                file_paths.update(_extract_paths(br, prefix="branch"))

        for val in data.get("validations") or []:
            if isinstance(val, dict):
                file_paths.update(_extract_paths(val, prefix="validation"))

        for path in file_paths:
            if _is_mapped(path) or _is_ignored(path):
                continue
            key_counts[path] += 1
            if path not in key_files:
                key_files[path] = []
            if yaml_file.name not in key_files[path]:
                key_files[path].append(yaml_file.name)

    unmapped: list[dict] = []
    for key, count in key_counts.most_common():
        unmapped.append({
            "key": key,
            "count": count,
            "files": key_files.get(key, []),
        })

    return unmapped


def _count_yaml_presence(pages_dir: Path, mapped_keys: dict[str, str]) -> dict[str, dict]:
    """Policz wystąpienia kluczy z mapped_keys w plikach stron."""
    totals: dict[str, dict] = {}
    for label in mapped_keys:
        totals[label] = {"yaml_present": 0, "files": []}

    if not pages_dir.exists():
        return totals

    for yaml_file in sorted(pages_dir.glob("p*.yaml")):
        data = _safe_yaml_load(yaml_file)
        if not isinstance(data, dict):
            continue

        regions = data.get("regions", []) or []
        columns = [c for r in regions if isinstance(r, dict) for c in ((r.get("columns") or []) + (r.get("report-columns") or []))]
        items = (data.get("page-items", []) or []) + (data.get("items", []) or [])
        processes = data.get("processes", []) or []
        computations = data.get("computations") or []
        dynamic_actions = data.get("dynamic-actions") or []
        buttons = data.get("buttons") or []
        branches = data.get("branches") or []
        validations = data.get("validations") or []

        for label in mapped_keys:
            if "." in label:
                sec, key_path = label.split(".", 1)
            else:
                sec, key_path = label, ""

            if sec == "region":
                containers = regions
            elif sec == "column":
                containers = columns
            elif sec in ("page-item", "item"):
                containers = items
            elif sec == "process":
                containers = processes
            elif sec == "computation":
                containers = computations
            elif sec in ("dynamic-action", "da"):
                containers = dynamic_actions
            elif sec == "button":
                containers = buttons
            elif sec == "branch":
                containers = branches
            elif sec == "validation":
                containers = validations
            elif sec == "page":
                containers = [data]
            else:
                containers = [data]

            for c in containers:
                if isinstance(c, dict) and (key_path == "" or _deep_get(c, key_path) is not None):
                    totals[label]["yaml_present"] += 1
                    totals[label]["files"].append(yaml_file.name)
                    break

    return totals


def _model_field_populated(app: ApexApp) -> dict[str, int]:
    """Policz ile modeli ma wypełnione pola zmapowane."""
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
            counts["region.source_table"] += 1 if r.source_table else 0
            counts["region.source_owner"] += 1 if r.source_owner else 0
            counts["region.source_sql"] += 1 if r.source_sql else 0
            counts["region.source_where"] += 1 if r.source_where else 0
            counts["region.page_items_to_submit"] += 1 if r.page_items_to_submit else 0
            counts["region.editable"] += 1 if r.editable else 0
            counts["region.allowed_operations"] += 1 if r.allowed_operations else 0
            counts["region.lost_update_type"] += 1 if r.lost_update_type else 0
            counts["region.server_side_condition"] += 1 if r.server_side_condition else 0
            counts["region.template_options"] += 1 if r.template_options else 0
            counts["region.pagination"] += 1 if r.pagination else 0
            counts["region.slot"] += 1 if r.slot else 0
            counts["region.sequence"] += 1 if r.sequence else 0
            counts["region.source_location"] += 1 if r.source_location else 0
            for c in r.columns:
                counts["column.link_text"] += 1 if c.link_text else 0
                counts["column.link_target"] += 1 if c.link_target else 0
                counts["column.master_region"] += 1 if c.master_region else 0
                counts["column.master_column"] += 1 if c.master_column else 0
                counts["column.column_alignment"] += 1 if c.column_alignment else 0
                counts["column.heading_alignment"] += 1 if c.heading_alignment else 0
                counts["column.sortable"] += 1 if c.sortable else 0
        for it in page.items:
            counts["page_item.label"] += 1 if it.label else 0
            counts["page_item.label_alignment"] += 1 if it.label_alignment else 0
            counts["page_item.value_required"] += 1 if it.value_required else 0
            counts["page_item.validation_max_length"] += 1 if it.validation_max_length else 0
            counts["page_item.source_primary_key"] += 1 if it.source_primary_key else 0
            counts["page_item.source_query_only"] += 1 if it.source_query_only else 0
            counts["page_item.form_region"] += 1 if it.form_region else 0
            counts["page_item.source_used"] += 1 if it.source_used else 0
            counts["page_item.lov"] += 1 if it.lov else 0
            counts["page_item.lov_display_null_value"] += 1 if it.lov_display_null_value else 0
            counts["page_item.lov_display_extra_values"] += 1 if it.lov_display_extra_values else 0
            counts["page_item.data_type"] += 1 if it.data_type else 0
            counts["page_item.storage"] += 1 if it.storage else 0
            counts["page_item.session_state_protection"] += 1 if it.session_state_protection else 0
            counts["page_item.store_encrypted"] += 1 if it.store_encrypted else 0
            counts["page_item.region"] += 1 if it.region else 0
        for p in page.processes:
            counts["process.error_display_location"] += 1 if p.error_display_location else 0
            counts["process.target_type"] += 1 if p.target_type else 0
            counts["process.return_primary_key_after_insert"] += 1 if p.return_primary_key_after_insert else 0
            counts["process.prevent_lost_updates"] += 1 if p.prevent_lost_updates else 0
            counts["process.lock_row"] += 1 if p.lock_row else 0
            counts["process.show_success_messages"] += 1 if p.show_success_messages else 0
            counts["process.success_message"] += 1 if p.success_message else 0
            counts["process.owner"] += 1 if p.owner else 0
            counts["process.package"] += 1 if p.package else 0
            counts["process.procedure_or_function"] += 1 if p.procedure_or_function else 0
        for button in page.buttons:
            counts["button.confirmation_message"] += 1 if button.confirmation_message else 0
            counts["button.confirmation_style"] += 1 if button.confirmation_style else 0
            counts["button.server_side_condition"] += 1 if button.server_side_condition else 0
        for action in page.dynamic_actions:
            counts["dynamic_action.event"] += 1 if action.event else 0
            counts["dynamic_action.selection_type"] += 1 if action.selection_type else 0
            counts["dynamic_action.client_side_condition"] += 1 if action.client_side_condition else 0
            for step in action.actions:
                counts["dynamic_action_step.maintain_pagination"] += 1 if step.maintain_pagination else 0
                counts["dynamic_action_step.show_processing"] += 1 if step.show_processing else 0
                counts["dynamic_action_step.items_to_submit"] += 1 if step.items_to_submit else 0

    # Shared components
    counts["shared.authentications"] = len(app.authentications)
    counts["shared.plugins"] = len(app.plugins)
    counts["shared.search_configs"] = len(app.search_configs)
    counts["shared.data_load_defs"] = len(app.data_load_defs)
    counts["shared.static_files"] = len(app.static_files)
    counts["shared.page_groups"] = len(app.page_groups)

    return dict(counts)


def generate_coverage_report(input_dir: str = "_data", coverage_config: str = "") -> dict:
    """Wygeneruj raport pokrycia mapowania.

    Args:
        input_dir: Katalog eksportu APEX
        coverage_config: Opcjonalna ścieżka do niestandardowych reguł pokrycia YAML

    Returns:
        Słownik ze statystykami mapowania i niezmapowanymi kluczami.
    """
    from apex_export_to_md.cli import find_app_root
    from apex_export_to_md.parser.page_parser import parse_all_pages
    from apex_export_to_md.parser.shared_parser import parse_shared_components

    app_root = find_app_root(Path(input_dir))
    pages_dir = app_root / "pages"
    shared_dir = app_root / "shared_components"

    # 1. Załaduj reguły pokrycia
    rules = load_coverage_rules(custom_path=coverage_config, input_dir=input_dir)
    mapped_keys = rules.get("mapped_keys", {})
    shared_files_rules = rules.get("shared_files", {})

    # 2. Policz wystąpienia zmapowanych kluczy YAML w plikach stron
    yaml_presence = _count_yaml_presence(pages_dir, mapped_keys)

    # 3. Skanuj pliki pod kątem niezmapowanych kluczy APEX
    unmapped_keys = crawl_unmapped_keys(pages_dir, rules)

    # 4. Załaduj modele przez parsery
    pages = parse_all_pages(pages_dir)
    shared = parse_shared_components(shared_dir)
    app = ApexApp(
        name="coverage", id="?", pages=pages, **shared,
    )
    model_counts = _model_field_populated(app)

    # 5. Zbuduj per-kategoria statystyki pokrycia
    categories: list[dict] = []
    for yaml_label, model_field in mapped_keys.items():
        yaml_count = yaml_presence.get(yaml_label, {}).get("yaml_present", 0)
        model_count = model_counts.get(model_field, 0)
        if yaml_count == 0:
            pct = 100.0
        else:
            pct = round(min(100.0, (model_count / max(yaml_count, 1)) * 100), 1)
            if model_count >= yaml_count:
                pct = 100.0
        categories.append({
            "category": yaml_label,
            "model_field": model_field,
            "yaml_present": yaml_count,
            "model_filled": model_count,
            "coverage_pct": pct,
        })

    # 6. Shared components status
    shared_status: list[dict] = []
    for label, rel_path in shared_files_rules.items():
        full = app_root / rel_path
        data = _safe_yaml_load(full)
        count = len(app.authentications) if label == "authentications" else \
                len(app.plugins) if label == "plugins" else \
                len(app.search_configs) if label == "search_configs" else \
                len(app.data_load_defs) if label == "data_load_defs" else \
                len(app.static_files) if label == "static_files" else \
                len(app.page_groups) if label == "page_groups" else 0
        shared_status.append({
            "component": label,
            "file": rel_path,
            "file_exists": full.exists(),
            "yaml_entries": len(data) if isinstance(data, list) else (1 if data else 0),
            "model_entries": count,
            "mapped": count > 0,
        })

    # 7. Podsumowanie
    mapped_cats = sum(1 for c in categories if c["yaml_present"] > 0 and c["model_filled"] > 0)
    unmapped_count = len(unmapped_keys)
    total_evaluated = mapped_cats + unmapped_count
    overall_pct = round((mapped_cats / total_evaluated * 100), 1) if total_evaluated > 0 else 100.0

    mapped_shared = sum(1 for s in shared_status if s["mapped"])
    source_shared = sum(1 for s in shared_status if s["file_exists"])

    return {
        "input_dir": str(app_root),
        "pages_count": len(pages),
        "overall_coverage_pct": overall_pct,
        "categories_mapped": f"{mapped_cats}/{total_evaluated}",
        "shared_mapped": f"{mapped_shared}/{source_shared}",
        "categories": categories,
        "shared_components": shared_status,
        "unmapped_keys": unmapped_keys,
        "unmapped_count": unmapped_count,
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
    lines.append("--- UNMAPPED / NEW APEX KEYS ---")
    unmapped = report.get("unmapped_keys", [])
    if not unmapped:
        lines.append("Brak niezmapowanych kluczy APEX.")
    else:
        lines.append(f"{'Klucz YAML':<50} {'Wystąpienia':>12} {'Przykłady':<20}")
        lines.append("-" * 85)
        for u in unmapped:
            sample_files = ", ".join(u["files"][:3])
            lines.append(f"{u['key']:<50} {u['count']:>12} {sample_files:<20}")
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def run_coverage(input_dir: str = "_data", output_dir: str = "_out",
                 as_json: bool = False, coverage_config: str = "") -> str:
    """Uruchom raport pokrycia i zapisz wynik.

    Returns:
        Ścieżka do zapisanego pliku raportu.
    """
    report = generate_coverage_report(input_dir, coverage_config=coverage_config)

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
    """Punkt wejścia: python -m apex_export_to_md.coverage_report [input] [--json] [--coverage-config path]."""
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(prog="apex_export_to_md.coverage_report",
                                     description="Raport pokrycia mapowania elementów APEX.")
    parser.add_argument("input_dir", nargs="?", default="_data")
    parser.add_argument("--output-dir", default="_out")
    parser.add_argument("--coverage-config", default="", help="Ścieżka do niestandardowego pliku reguł pokrycia YAML")
    parser.add_argument("--json", action="store_true", help="Wyjście JSON zamiast tekstu")
    args = parser.parse_args()
    path = run_coverage(args.input_dir, args.output_dir, as_json=args.json, coverage_config=args.coverage_config)
    print(f"Raport pokrycia zapisany: {path}")
    report = generate_coverage_report(args.input_dir, coverage_config=args.coverage_config)
    print(format_report_text(report))


if __name__ == "__main__":
    main()
