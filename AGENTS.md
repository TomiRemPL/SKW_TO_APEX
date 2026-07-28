# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Summary

Python CLI tool (`apex_export_to_md`) that converts Oracle APEX application exports (YAML readable format) and DDL files into multiple documentation formats (Markdown, HTML, SQL migration scripts). The APEX application itself is an Internal Control Management and Audit System (Polish UI).

## Quick Commands

```bash
# Run the CLI (default: reads from _data/, outputs to _out/)
python -m apex_export_to_md

# Run with options
python -m apex_export_to_md _data --format llm --verbose

# Start the web GUI (FastAPI on port 8338)
python -m apex_export_to_md --gui

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_page_parser.py -v
```

## Architecture

Pipeline pattern with strict layer separation:

```text
YAML files → Parser → [ApexApp model] → Filter → Renderer → output files
DDL file  → DDL Parser → [DDLSchema model] → DDL Renderer → output files
```

Key directories:

- `apex_export_to_md/parser/` — YAML and DDL parsing (input)
- `apex_export_to_md/models/` — Dataclasses (`ApexApp`, `ApexPage`, `Region`, `DDLSchema`, etc.)
- `apex_export_to_md/filters/` — Page filtering heuristics
- `apex_export_to_md/renderers/` — Output formatters (inherit from `BaseRenderer`)
- `apex_export_to_md/gui/` — FastAPI web interface
- `_data/` — Source data (APEX YAML export + DDL SQL)
- `_out/` — Generated output (timestamped files)

## Conventions

- **Language:** Code comments, docstrings, CLI help, and UI text are in **Polish**
- **Python version:** 3.10+ (uses `X | Y` union syntax, `list[T]` generics)
- **Dependencies:** Minimal — PyYAML, pytest, oracledb, FastAPI, uvicorn, jinja2
- **No build system:** Run directly with `python -m`. No setup.py/pyproject.toml packaging
- **Testing:** pytest with fixtures in `tests/conftest.py`. Test file names mirror source modules
- **Renderers:** New output formats subclass `BaseRenderer` and implement `render(app: ApexApp) -> str`
- **Config:** All settings flow through `AppConfig` dataclass. CLI args → `AppConfig` → pipeline

## Critical YAML & Renderer Patterns

### Using `safe_get()` for YAML Access — **REQUIRED**

All YAML access **must** use `safe_get()` from [apex_export_to_md/parser/yaml_helpers.py](apex_export_to_md/parser/yaml_helpers.py). This prevents KeyError/TypeError on missing keys and handles None gracefully.

**Pattern:**

```python
from apex_export_to_md.parser.yaml_helpers import safe_get, safe_get_str, safe_get_int

# Deeply nested YAML keys (dots separate path components)
name = safe_get_str(region_dict, "identification.name", default="Unknown")
col_type = safe_get(column_dict, "identification.type")
is_pk = safe_get_int(column_dict, "source.primary-key", default=0)
```

**Why:** APEX YAML export uses nested dictionaries. Safe helpers strip APEX ID suffixes (e.g., `"Name # 12345"` → `"Name"`), handle missing keys, and provide type conversion.

### Adding a New Renderer

All renderers inherit from `BaseRenderer` in [apex_export_to_md/renderers/base_renderer.py](apex_export_to_md/renderers/base_renderer.py). Template:

```python
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp

class MyRenderer(BaseRenderer):
    """Twój opis w języku polskim."""
    
    def render(self, app: ApexApp) -> str:
        """Generuj tekst wyjściowy."""
        output = []
        # Logika transformacji ApexApp → tekst
        return "\n".join(output)
```

**Steps:** (1) Subclass `BaseRenderer` in new file under `apex_export_to_md/renderers/` (2) Register in CLI at `apex_export_to_md/cli.py` in renderer selection logic (3) Add test file `tests/test_your_renderer.py` using pytest fixtures from [tests/conftest.py](tests/conftest.py)

## AppConfig Reference

| Pole | Typ | Domyślnie | Opis |
| --- | --- | --- | --- |
| `input_dir` | str | `"_data"` | Katalog z APEX export + DDL |
| `output_dir` | str | `"_out"` | Katalog dla plików wyjściowych |
| `output_prefix` | str | `"apex_export"` | Prefiks nazw plików (przed timestampem) |
| `ddl_file` | str | `""` | Bezpośrednia ścieżka do DDL (opcjonalna) |
| `output_format` | str | `"both"` | Dozwolone: `"both"`, `"human"`, `"llm"` |
| `include_code` | str | `"full"` | Dozwolone: `"full"`, `"summary"`, `"none"` |
| `page_filter` | str | `"auto"` | Tryb filtra: `"auto"` \| `"all"` \| `"prefix:X"` \| `"ids:1,2,3"` |
| `extra_pages` | list[int] | `[]` | ID stron do jawnego włączenia mimo filtra |
| `generate_ddl` | bool | `False` | Czy generować skrypt DDL |
| `generate_migration` | bool | `False` | Czy generować skrypt migracji |
| `fetch_ddl_from_db` | bool | `False` | Czy pobierać DDL z bazy (wymaga `db_connection`) |
| `include_layout` | bool | `False` | Czy uwzględniać informacje o layoutzie |
| `include_shared_components` | bool | `True` | Czy exportować komponenty wspólne (LOV, scheme, etc.) |
| `verbose` | bool | `False` | Czy drukować logi debug |

## File Naming

Output files use timestamp prefix: `YYYYMMDD_HHMMSS_{output_prefix}_{renderer_suffix}.{ext}`

## Database Context

See [CLAUDE.md](CLAUDE.md) for full Oracle APEX application context (tables, PL/SQL packages, security model). The DDL is in `_data/skw_to_apex_DDL_1.sql`.

## Common Pitfalls

- YAML keys use hyphens (`page-group`, `source-table`), model fields use underscores
- `yaml_helpers.py` provides `safe_get()` for deeply nested YAML access — always use it
- Page filter "auto" mode excludes standard APEX admin pages; check `config.py` for heuristics
- The `_data/readable/application/` structure mirrors APEX's own export layout

<!-- lean-ctx -->
## lean-ctx

Prefer lean-ctx MCP tools over native equivalents for token savings:
`ctx_read` > Read/cat, `ctx_search` > Grep/rg, `ctx_shell` > bash, `ctx_tree` > ls/find.
Native Edit/Write/Glob stay as-is; use `ctx_edit` only when Edit needs an unavailable Read.
Full rules: LEAN-CTX.md (open on demand — do not auto-load).
<!-- /lean-ctx -->
