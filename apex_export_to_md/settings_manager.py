"""Zarządzanie ustawieniami użytkownika — zapis/odczyt do pliku JSON.

Ustawienia zapisywane w ~/.apex_export_to_md/settings.json.
Hasło do bazy danych NIE jest zapisywane — pytane przy każdym uruchomieniu.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SETTINGS_DIR = Path.home() / ".apex_export_to_md"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

# Domyślne wartości ustawień
DEFAULT_SETTINGS: dict[str, Any] = {
    "input_dir": "_data",
    "output_dir": "_out",
    "output_prefix": "apex_export",
    "output_format": "both",
    "include_code": "full",
    "page_filter": "auto",
    "extra_pages": "",
    "include_internal_ids": False,
    "include_layout": False,
    "include_shared_components": True,
    "generate_ddl": False,
    "generate_migration": False,
    "db_connection": "",  # connection string BEZ hasła (np. user@host:1521/service)
    "verbose": False,
}

# Klucze które NIE mogą być zapisywane (bezpieczeństwo)
FORBIDDEN_KEYS = {"db_password", "password"}


def load_settings() -> dict[str, Any]:
    """Wczytaj ustawienia z pliku JSON. Zwraca domyślne jeśli plik nie istnieje."""
    if not SETTINGS_FILE.exists():
        logger.debug("Plik ustawień nie istnieje, używam domyślnych.")
        return dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        # Scal z domyślnymi (nowe klucze)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        # Usuń zabronione klucze
        for key in FORBIDDEN_KEYS:
            merged.pop(key, None)
        return merged
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Błąd odczytu ustawień: %s. Używam domyślnych.", e)
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    """Zapisz ustawienia do pliku JSON. Pomija hasła."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    # Odfiltruj zabronione klucze
    safe_settings = {k: v for k, v in settings.items() if k not in FORBIDDEN_KEYS}
    SETTINGS_FILE.write_text(
        json.dumps(safe_settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Ustawienia zapisane w: %s", SETTINGS_FILE)


def get_settings_path() -> Path:
    """Zwróć ścieżkę do pliku ustawień."""
    return SETTINGS_FILE
