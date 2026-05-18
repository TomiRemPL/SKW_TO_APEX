"""Testy CLI (parsowanie argumentów)."""
from apex_export_to_md.cli import parse_args


def test_parse_args_domyslne():
    """Wywołanie bez argumentów — domyślne wartości."""
    args = parse_args([])
    assert args.input_dir == "_data"
    assert args.output_dir == "_out"
    assert args.format == "both"
    assert args.include_code == "full"
    assert args.page_filter == "auto"


def test_parse_args_z_sciezka():
    """Wywołanie z podaną ścieżką."""
    args = parse_args(["/path/to/export"])
    assert args.input_dir == "/path/to/export"
    assert args.output_dir == "_out"


def test_parse_args_pelne():
    """Pełne wywołanie z wszystkimi opcjami."""
    args = parse_args([
        "/path",
        "--output-dir", "/out",
        "--output-prefix", "my_export",
        "--format", "llm",
        "--include-code", "none",
        "--page-filter", "prefix:DAW_",
        "--extra-pages", "1,9999",
        "--include-internal-ids",
        "--include-layout",
        "--no-shared-components",
        "--verbose",
    ])
    assert args.output_dir == "/out"
    assert args.output_prefix == "my_export"
    assert args.format == "llm"
    assert args.include_code == "none"
    assert args.page_filter == "prefix:DAW_"
    assert args.extra_pages == "1,9999"
    assert args.include_internal_ids is True
    assert args.include_layout is True
    assert args.no_shared_components is True
    assert args.verbose is True
