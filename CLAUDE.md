# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **two distinct components**:

1. **Oracle APEX 24.1 Application** — Internal Control Management and Audit System (Polish: System Kontroli Wewnętrznych), built on Oracle Database with schema `DAW`. UI language is Polish.
2. **Python Documentation Tool** — CLI tool (`apex_export_to_md`) that converts APEX exports (YAML) and DDL files into multiple documentation formats (Markdown, HTML, SQL migration scripts).

Most development work will be on the **Python tool**. The APEX application data serves as input for the tool.

## Repository Structure

**Python Tool:**
- `apex_export_to_md/` — Main Python package
  - `cli.py` — Entry point, argument parsing, pipeline orchestration
  - `config.py` — `AppConfig` dataclass and filtering heuristics
  - `parser/` — YAML and DDL parsing (input layer)
  - `models/` — Dataclasses (`ApexApp`, `ApexPage`, `Region`, `DDLSchema`, etc.)
  - `filters/` — Page filtering logic
  - `renderers/` — Output formatters (all inherit from `BaseRenderer`)
  - `gui/` — FastAPI web interface (port 8338)
- `tests/` — pytest test suite (mirrors source structure)
- `_out/` — Generated output files (timestamped)

**APEX Application Data:**
- `_data/skw_to_apex_DDL_1.sql` — Full database schema: tables, views, PL/SQL packages
- `_data/readable/application/` — APEX application export (YAML format, app ID 160, alias START338)
  - `f338.yaml` — Root application definition
  - `pages/` — Individual APEX page definitions (35+ pages)
  - `shared_components/` — LOVs, auth schemes, navigation, ACL roles

## Common Commands

**Run the Python tool:**
```bash
# Basic usage (reads _data/, outputs to _out/)
python -m apex_export_to_md

# With options
python -m apex_export_to_md _data --format llm --verbose --page-filter prefix:DAW_

# Automatic DDL fetching from Oracle database
python -m apex_export_to_md _data --fetch-ddl-from-db --ddl-keyword "*/OnSite*/" --db-connection "user/pass@host:1521/service"

# Start web GUI (FastAPI on port 8338)
python -m apex_export_to_md --gui

# Windows shortcut with .env loading
scripts\start-gui-with-env.bat
```

**Run tests:**
```bash
# All tests
pytest tests/ -v

# Specific test module
pytest tests/test_page_parser.py -v
pytest tests/test_human_renderer.py -v
```

**Setup:**
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate    # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

## Python Tool Architecture

Pipeline pattern with strict layer separation:

```
YAML files → Parser → [ApexApp model] → Filter → Renderer → output files
DDL file  → DDL Parser → [DDLSchema model] → DDL Renderer → output files
```

**Key principles:**
- Config flows through `AppConfig` dataclass: CLI args → `AppConfig` → pipeline
- New output formats subclass `BaseRenderer` and implement `render(app: ApexApp) -> str`
- YAML keys use hyphens (`page-group`), model fields use underscores (`page_group`)
- Use `yaml_helpers.safe_get()` for deeply nested YAML access
- All code/docs/UI text in **Polish**
- Python 3.10+ required (uses `X | Y` syntax, `list[T]` generics)
- No build system — run directly with `python -m apex_export_to_md`

**Output file naming:** `YYYYMMDD_HHMMSS_{output_prefix}_{suffix}.{ext}`

## APEX Application Deployment

There is no build pipeline for the APEX app. Deployment is manual:

1. Execute `_data/skw_to_apex_DDL_1.sql` against the Oracle database (schema `DAW`)
2. Import `_data/readable/application/` into Oracle APEX using the APEX import tool or `apex export`/`apex import` CLI

## Database Architecture

**Core Tables:**

- `B_AUDYT` — Audit records; lifecycle: `Otwarty` → `Zamrozony` → `Zakonczony`
- `B_KONTROLA` — Control definitions (sourced from external SCOPE_DEFINITION Excel); key: `REFERENCE_ID`
- `B_KONTROLA_HIST` — Audit trail of control field changes
- `B_KONTROLA_IMPORT` — Staging table for Excel imports
- `B_AUDYT_KONTROLA` — Junction: audits ↔ controls
- `B_ANKIETA` / `B_OCENA` — Survey responses and evaluation scores
- `B_SL_C_PYTANIE` / `B_SL_C_PYTANIE_DZIEDZINA` — Question and domain dictionaries

**Key Views:**

- `B_V_AUDYT_KONTROLE` — Audit controls with full joined data
- `B_V_IMPORT_STATYSTYKI` — Import run statistics

## PL/SQL Packages

**`PKG_AUDYT`** — Audit lifecycle and permissions:

- `UTWORZ_AUDYT` — Create audit
- `DODAJ_KONTROLE` / `USUN_KONTROLE` — Add/remove controls (only when status=`Otwarty`)
- `ZAMROZ_AUDYT` / `ZAKONCZ_AUDYT` — Freeze/close (mission leader only)
- `SPRAWDZ_UPRAWNIENIA(p_audyt_id)` — Returns `SZEF` / `AUDYTOR` / `BRAK`
- `MOZE_EDYTOWAC(p_audyt_id)` — Returns boolean edit permission for current session user

**`PKG_IMPORT_KONTROLI`** — Monthly Excel import into `B_KONTROLA`:

- `WYKONAJ_IMPORT` — Main entry point; reads from `B_KONTROLA_IMPORT` staging table
- `WALIDUJ_STAGING` — Validates staging rows before processing
- `CZY_ROZNE(a, b)` — NULL-safe varchar comparison helper
- On run: inserts new records, updates changed records (archiving previous version to `B_KONTROLA_HIST`), sets `DATA_DEZAKTYWACJI` for records absent from the new import

## Security & Auth

- **Authentication:** ADFS (corporate Active Directory via APEX authentication scheme)
- **Session user:** Available via `APP_USER`; matched to `SZEF_MISJI_LOGIN` and `AUDYTORZY_LOGINY` columns in `B_AUDYT`
- **Authorization:** Role-based (ACL_ONLY scope); field-level edit rights tied to audit team membership
- **Other:** Browser cache disabled, embed-in-frames denied, strict-origin referrer policy

## APEX Page Groups

Pages `p10000`–`p10061` cover main audit management. Pages `p00000`–`p09999` are system/admin. Page `p20010` covers secondary features.

<!-- selvedge:start -->
## Selvedge � change tracking

You have access to Selvedge (MCP server: `selvedge`) for change tracking.

**Rules:**

- Call `selvedge.log_change` immediately after adding, modifying, or
  removing any DB column, table, function, API endpoint, dependency,
  or env variable.
- Set `reasoning` to the user's original request or the problem being
  solved. Write at least one full sentence � the server will warn on
  empty, very short, or generic values like "user request" or "done".
  Good example: "User asked to add 2FA � needs phone number to send
  SMS verification codes."
- Set `agent` to "claude-code" (or whichever agent you are).
- Set `session_id` if you have access to the current session/conversation ID.
- Set `git_commit` to the commit hash once you know it.
- For multi-entity changes (e.g. adding a whole feature), set a shared
  `changeset_id` on all related `log_change` calls � use a short slug
  like `add-stripe-billing`. This lets anyone query the full scope of
  the change with `selvedge.changeset()`.
- Before modifying an entity, call `selvedge.diff` or `selvedge.blame`
  to understand its history and avoid conflicting with past decisions.
<!-- selvedge:end -->
