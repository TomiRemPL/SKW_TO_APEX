---
name: new-renderer
description: 'Tworzy nowy renderer wyjściowy dla apex_export_to_md. Użyj gdy potrzebujesz nowego formatu eksportu (np. JSON, CSV, PDF). Prowadzi przez: subklasowanie BaseRenderer, rejestrację w CLI, dodanie testów.'
---

# Nowy Renderer

## Kiedy użyć

- Dodajesz nowy format wyjściowy do pipeline'u
- Potrzebujesz alternatywnej reprezentacji danych APEX/DDL

## Procedura

### 1. Utwórz plik renderera

Ścieżka: `apex_export_to_md/renderers/{nazwa}_renderer.py`

Szablon:

```python
"""Renderer {OPIS} — {co generuje}."""
from __future__ import annotations

from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp
from apex_export_to_md.renderers.base_renderer import BaseRenderer


class {Nazwa}Renderer(BaseRenderer):
    """Generuje {format} z modelu ApexApp."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny tekst wyjściowy."""
        lines: list[str] = []
        # ... implementacja
        return "\n".join(lines)
```

### 2. Zarejestruj w CLI

W `apex_export_to_md/cli.py`, w funkcji `run_pipeline()`:

1. Dodaj import na górze pliku
2. Dodaj wywołanie renderera po linii z `HumanRenderer` w funkcji `run_pipeline()`, używając identycznego wzorca: `result = {Nazwa}Renderer(config).render(app)` oraz zapisu do pliku z sufiksem `_{format}.{ext}`
3. Użyj odpowiedniego sufiksu pliku w nazwie wyjściowej

### 3. Dodaj testy

Ścieżka: `tests/test_{nazwa}_renderer.py`

Minimalny test:

```python
"""Testy renderera {nazwa}."""
from apex_export_to_md.config import AppConfig
from apex_export_to_md.renderers.{nazwa}_renderer import {Nazwa}Renderer


def test_renderuje_podstawowy_eksport(sample_app):
    """Sprawdza, że renderer generuje poprawny output."""
    config = AppConfig()
    renderer = {Nazwa}Renderer(config)
    result = renderer.render(sample_app)
    assert len(result) > 0
    # Dodaj asercje specyficzne dla formatu
```

Fixture `sample_app` jest zdefiniowana w `tests/conftest.py`.

### 4. Uruchom testy

```bash
python -m pytest tests/test_{nazwa}_renderer.py -v
```

## Konwencje

- Docstringi i komentarze po polsku
- Nazwa klasy: `{Format}Renderer` (PascalCase)
- Nazwa pliku: `{format}_renderer.py` (snake_case)
- Sufiks wyjściowy: `_{format}.{ext}` (np. `_json.json`)
- Renderer operuje na modelu `ApexApp` lub `DDLSchema` — nigdy nie czyta YAML bezpośrednio
- Jeśli renderer dotyczy DDL, użyj `DDLSchema` zamiast `ApexApp` w sygnaturze metody `render`. Nie mieszaj obu w jednym rendererze — utwórz oddzielne klasy

## Istniejące renderery (do wzorowania)

| Renderer | Plik | Opis |
|----------|------|------|
| `HumanRenderer` | `human_renderer.py` | Markdown czytelny dla człowieka |
| `LLMRenderer` | `llm_renderer.py` | Skondensowany Markdown dla LLM |
| `HTMLRenderer` | `html_renderer.py` | Interaktywna dokumentacja HTML |
| `DDLHumanRenderer` | `ddl_human_renderer.py` | DDL w formacie Markdown |
| `DDLScriptRenderer` | `ddl_script_renderer.py` | Czysty SQL do wykonania |
| `MigrationRenderer` | `migration_renderer.py` | Skrypt migracyjny z danymi |
| `RollbackRenderer` | `rollback_renderer.py` | Skrypt cofania migracji |
