"""Helpery do bezpiecznego odczytu zagnieżdżonych struktur YAML.

Eksport APEX używa głęboko zagnieżdżonych kluczy (np. identification.name,
source.table-name). Te funkcje zapobiegają KeyError/TypeError przy brakujących
kluczach i zapewniają spójne domyślne wartości.
"""
from __future__ import annotations
import re
from typing import Any


def safe_get(data: dict | None, key_path: str, default: Any = None) -> Any:
    """Bezpieczne odczytanie wartości z zagnieżdżonego słownika.

    Args:
        data: Słownik źródłowy (może być None)
        key_path: Ścieżka klucza z kropkami, np. "identification.name"
        default: Wartość domyślna gdy klucz nie istnieje

    Returns:
        Wartość pod podaną ścieżką lub default
    """
    if data is None:
        return default

    keys = key_path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def safe_get_str(
    data: dict | None,
    key_path: str,
    default: str | None = None,
    strip_id: bool = True,
) -> str | None:
    """Odczytaj wartość tekstową, opcjonalnie usuwając sufiks ID APEX.

    Wiele wartości YAML zawiera komentarz z ID, np.:
        'Administration # 52840988022029242'
    Parametr strip_id=True obcina ten sufiks.
    """
    value = safe_get(data, key_path, default)
    if value is None:
        return default
    value = str(value)
    if strip_id:
        value = strip_apex_id(value)
    return value


def safe_get_int(data: dict | None, key_path: str, default: int = 0) -> int:
    """Odczytaj wartość całkowitą."""
    value = safe_get(data, key_path)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_get_bool(data: dict | None, key_path: str, default: bool = False) -> bool:
    """Odczytaj wartość logiczną."""
    value = safe_get(data, key_path)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1")
    return default


def safe_get_list(data: dict | None, key_path: str) -> list:
    """Odczytaj listę (pustą gdy brak klucza)."""
    value = safe_get(data, key_path)
    if isinstance(value, list):
        return value
    return []


# Wzorzec: tekst, opcjonalnie zakończony " # <cyfry>" (dowolna liczba cyfr)
_APEX_ID_SUFFIX = re.compile(r"\s*#\s*\d+\s*$")


def strip_apex_id(value: str | None) -> str | None:
    """Usuń sufiks ID APEX z tekstu, np. 'Foo # 123456' → 'Foo'."""
    if value is None:
        return None
    return _APEX_ID_SUFFIX.sub("", value).strip()


def collect_build_options(data: dict) -> list[str]:
    """Zbierz rekurencyjnie wszystkie wartości klucza 'build-option' ze struktury.

    Zwraca listę nazw build-options (z obciętymi ID APEX).
    """
    results: list[str] = []
    _collect_bo_recursive(data, results)
    return results


def _collect_bo_recursive(obj: Any, results: list[str]) -> None:
    """Rekurencyjne przeszukiwanie struktury w poszukiwaniu 'build-option'."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "build-option" and isinstance(value, str):
                cleaned = strip_apex_id(value)
                if cleaned and cleaned not in results:
                    results.append(cleaned)
            else:
                _collect_bo_recursive(value, results)
    elif isinstance(obj, list):
        for item in obj:
            _collect_bo_recursive(item, results)


def clean_raw_attributes(data: dict, extra_skip_keys: set[str] | None = None) -> dict:
    """Przygotuj surowe atrybuty YAML do przechowania w modelu.

    Usuwa ID APEX z wartości tekstowych, usuwa klucz 'id' oraz
    wybrane klucze techniczne. Filtruje None i puste wartości.
    """
    if not isinstance(data, dict):
        return {}
    skip = {"id"}
    if extra_skip_keys:
        skip |= extra_skip_keys
    return _deep_clean(data, skip)


def _deep_clean(obj: Any, skip_keys: set[str]) -> Any:
    """Rekurencyjnie oczyszcza strukturę z ID APEX i technicznych kluczy."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key in skip_keys:
                continue
            cleaned = _deep_clean(value, skip_keys)
            if cleaned is not None and cleaned != "" and cleaned != [] and cleaned != {}:
                result[key] = cleaned
        return result if result else {}
    elif isinstance(obj, list):
        cleaned = [_deep_clean(item, skip_keys) for item in obj]
        cleaned = [item for item in cleaned if item is not None and item != ""]
        return cleaned if cleaned else []
    elif isinstance(obj, str):
        cleaned = strip_apex_id(obj)
        return cleaned if cleaned else None
    return obj
