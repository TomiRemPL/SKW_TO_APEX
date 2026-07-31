"""Testy skryptu raportu pokrycia (coverage_report.py)."""
from pathlib import Path
from apex_export_to_md.coverage_report import (
    generate_coverage_report, format_report_text, run_coverage,
    load_coverage_rules, crawl_unmapped_keys,
)


def test_generate_coverage_report_real_data():
    """Sprawdza wygenerowanie raportu pokrycia dla danych z _data/."""
    data_dir = Path("_data")
    if not (data_dir / "readable" / "application" / "pages").exists():
        return  # pomiń gdy brak _data
    report = generate_coverage_report("_data")
    assert report["pages_count"] > 0
    assert report["overall_coverage_pct"] >= 0.0
    assert len(report["categories"]) >= 21
    assert len(report["shared_components"]) == 6
    assert "unmapped_keys" in report
    assert report["unmapped_count"] >= 0


def test_load_coverage_rules_builtin():
    """Sprawdza wczytywanie wbudowanych reguł coverage_rules.yaml."""
    rules = load_coverage_rules()
    assert "mapped_keys" in rules
    assert "region.server-side-condition" in rules["mapped_keys"]
    assert "ignore_keys" in rules
    assert "accessibility" in rules["ignore_keys"]
    assert "shared_files" in rules
    assert "authentications" in rules["shared_files"]


def test_load_coverage_rules_custom_path(tmp_path):
    """Sprawdza nadpisywanie i łączenie reguł z plikiem niestandardowym."""
    custom_yaml = tmp_path / "custom_rules.yaml"
    custom_yaml.write_text("""
mapped_keys:
  region.custom-feature: region.custom_feature
ignore_keys:
  - custom-noise-key
""", encoding="utf-8")

    rules = load_coverage_rules(custom_path=str(custom_yaml))
    assert "region.custom-feature" in rules["mapped_keys"]
    assert "region.server-side-condition" in rules["mapped_keys"]
    assert "custom-noise-key" in rules["ignore_keys"]
    assert "accessibility" in rules["ignore_keys"]


def test_crawl_unmapped_keys_synthetic(tmp_path):
    """Sprawdza wykrywanie niezmapowanych kluczy w syntetycznym pliku YAML."""
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir(parents=True)

    p1 = pages_dir / "p00001.yaml"
    p1.write_text("""
identification:
  name: "Test Page"
regions:
  - identification:
      name: "Header Region"
    new-apex-feature:
      setting-a: "enabled"
""", encoding="utf-8")

    rules = load_coverage_rules()
    unmapped = crawl_unmapped_keys(pages_dir, rules)

    keys = [u["key"] for u in unmapped]
    assert "region.new-apex-feature.setting-a" in keys
    found = next(u for u in unmapped if u["key"] == "region.new-apex-feature.setting-a")
    assert found["count"] == 1
    assert "p00001.yaml" in found["files"]


def test_format_report_text():
    """Sprawdza formatowanie tekstowe raportu."""
    mock_report = {
        "input_dir": "_data/test",
        "pages_count": 10,
        "overall_coverage_pct": 100.0,
        "categories_mapped": "5/5",
        "shared_mapped": "6/6",
        "categories": [
            {
                "category": "region.server-side-condition",
                "model_field": "region.server_side_condition",
                "yaml_present": 5,
                "model_filled": 5,
                "coverage_pct": 100.0,
            }
        ],
        "shared_components": [
            {
                "component": "authentications",
                "file": "shared_components/authentications.yaml",
                "file_exists": True,
                "yaml_entries": 3,
                "model_entries": 3,
                "mapped": True,
            }
        ],
        "unmapped_keys": [
            {
                "key": "page.new-ai-assistant.enabled",
                "count": 2,
                "files": ["p00001.yaml"],
            }
        ],
    }
    text = format_report_text(mock_report)
    assert "RAPORT POKRYCIA MAPOWANIA" in text
    assert "100.0%" in text
    assert "region.server-side-condition" in text
    assert "authentications" in text
    assert "UNMAPPED / NEW APEX KEYS" in text
    assert "page.new-ai-assistant.enabled" in text


def test_run_coverage_tmp(tmp_path):
    """Sprawdza zapisanie pliku raportu."""
    out_file = run_coverage("_data", str(tmp_path))
    assert Path(out_file).exists()
    assert Path(out_file).stat().st_size > 0
