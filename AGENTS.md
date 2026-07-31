# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Summary

Python CLI tool (`apex_export_to_md`) that converts Oracle APEX application exports (YAML readable format) and DDL files into multiple documentation formats (Markdown, HTML, SQL migration scripts). The APEX application itself is an Internal Control Management and Audit System (Polish UI).

## Quick Commands

```bash
# Run CLI (reads from _data/, outputs to _out/)
python -m apex_export_to_md

# Run CLI with custom options
python -m apex_export_to_md _data --format llm --verbose

# Start web GUI (FastAPI on http://localhost:8338)
python -m apex_export_to_md --gui

# Run test suite
python -m pytest tests/ -v
```

## Architecture

Pipeline pattern with strict layer separation:

```text
YAML files → Parser → [ApexApp model] → Filter → Renderer → Output files
DDL file   → DDL Parser → [DDLSchema model] → DDL Renderer → Output files
```

Key directories:

- `apex_export_to_md/parser/` — YAML and DDL parsers
- `apex_export_to_md/models/` — Dataclasses (`ApexApp`, `ApexPage`, `Region`, `DDLSchema`, etc.)
- `apex_export_to_md/filters/` — Page filtering logic
- `apex_export_to_md/renderers/` — Output formatters (subclass `BaseRenderer`)
- `apex_export_to_md/gui/` — FastAPI web interface
- `_data/` — Input source data (APEX YAML export + DDL SQL)
- `_out/` — Output generated files (timestamped: `YYYYMMDD_HHMMSS_{prefix}_{suffix}.{ext}`)

## Key Conventions

- **Language:** Docstrings, code comments, CLI help, and UI text are in **Polish**.
- **Python version:** 3.10+ (type union syntax `X | Y`, built-in generics `list[T]`).
- **Dependencies:** Minimal — PyYAML, pytest, oracledb, FastAPI, uvicorn, jinja2.
- **No package build:** Run directly via `python -m`. No `setup.py` / `pyproject.toml`.
- **Testing:** `pytest` using fixtures in `tests/conftest.py`.
- **YAML keys vs Models:** YAML uses hyphens (`page-group`, `source-table`); dataclass models use underscores.

## Critical YAML & Renderer Patterns

### Using `safe_get()` for YAML Access — **REQUIRED**

All YAML parsing **must** use helpers from `apex_export_to_md.parser.yaml_helpers` (`safe_get`, `safe_get_str`, `safe_get_int`). This handles nested dicts, strips APEX ID suffixes (e.g., `"Name # 12345"` → `"Name"`), and prevents missing key errors.

```python
from apex_export_to_md.parser.yaml_helpers import safe_get, safe_get_str, safe_get_int

name = safe_get_str(region_dict, "identification.name", default="Unknown")
col_type = safe_get(column_dict, "identification.type")
is_pk = safe_get_int(column_dict, "source.primary-key", default=0)
```

### Adding a New Renderer

Subclass `BaseRenderer` in `apex_export_to_md/renderers/`:

```python
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp

class MyRenderer(BaseRenderer):
    """Opis w języku polskim."""
    
    def render(self, app: ApexApp) -> str:
        return "\n".join(output)
```

Register in `apex_export_to_md/cli.py` and add unit tests under `tests/`.

## Configuration Overview (`AppConfig`)

Key options in `AppConfig` dataclass (`config.py`):
- `input_dir` (`_data`), `output_dir` (`_out`), `output_prefix` (`apex_export`)
- `output_format`: `"both"` | `"human"` | `"llm"`
- `include_code`: `"full"` | `"summary"` | `"none"`
- `page_filter`: `"auto"` (excludes APEX admin pages) | `"all"` | `"prefix:X"` | `"ids:1,2,3"`
- `extra_pages`: list of page IDs to forcefully include
- `generate_ddl`, `generate_migration`, `include_layout`, `include_shared_components`

## Database Context

See [CLAUDE.md](CLAUDE.md) for database tables, PL/SQL packages, and security model details. Schema DDL is in `_data/skw_to_apex_DDL_1.sql`.

<!-- lean-ctx -->
## lean-ctx

Prefer lean-ctx MCP tools over native equivalents for token savings:
`ctx_read` > Read/cat, `ctx_search` > Grep/rg, `ctx_shell` > bash, `ctx_tree` > ls/find.
Native Edit/Write/Glob stay as-is; use `ctx_edit` only when Edit needs an unavailable Read.
Full rules: LEAN-CTX.md (open on demand — do not auto-load).
<!-- /lean-ctx -->
