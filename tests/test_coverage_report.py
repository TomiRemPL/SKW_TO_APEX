"""Testy skryptu raportu pokrycia (coverage_report.py)."""
from pathlib import Path
from apex_export_to_md.coverage_report import (
    generate_coverage_report, format_report_text, run_coverage,
)


def test_generate_coverage_report_real_data():
    """Sprawdza wygenerowanie raportu pokrycia dla danych z _data/."""
    data_dir = Path("_data")
    if not (data_dir / "readable" / "application" / "pages").exists():
        return  # pomiń gdy brak _data
    report = generate_coverage_report("_data")
    assert report["pages_count"] > 0
    assert report["overall_coverage_pct"] >= 90.0
    assert len(report["categories"]) == 21
    assert len(report["shared_components"]) == 6


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
    }
    text = format_report_text(mock_report)
    assert "RAPORT POKRYCIA MAPOWANIA" in text
    assert "100.0%" in text
    assert "region.server-side-condition" in text
    assert "authentications" in text


def test_run_coverage_tmp(tmp_path):
    """Sprawdza zapisanie pliku raportu."""
    out_file = run_coverage("_data", str(tmp_path))
    assert Path(out_file).exists()
    assert Path(out_file).stat().st_size > 0
