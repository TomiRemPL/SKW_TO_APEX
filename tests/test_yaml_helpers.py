"""Testy helperów do bezpiecznego odczytu YAML."""
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_int, safe_get_bool, safe_get_list,
    strip_apex_id, collect_build_options,
)


def test_safe_get_klucz_prosty():
    data = {"name": "test"}
    assert safe_get(data, "name") == "test"


def test_safe_get_klucz_zagniezdony():
    data = {"identification": {"name": "Foo", "title": "Bar"}}
    assert safe_get(data, "identification.name") == "Foo"
    assert safe_get(data, "identification.title") == "Bar"


def test_safe_get_brakujacy_klucz():
    data = {"a": {"b": 1}}
    assert safe_get(data, "a.c") is None
    assert safe_get(data, "x.y.z") is None
    assert safe_get(data, "a.c", "default") == "default"


def test_safe_get_str_obcina_id_apex():
    """Tekst z komentarzem ID APEX (np. 'Administration # 123456') → 'Administration'."""
    data = {"page-group": "Administration # 52840988022029242"}
    assert safe_get_str(data, "page-group", strip_id=True) == "Administration"


def test_safe_get_str_bez_obcinania():
    data = {"page-group": "Administration # 52840988022029242"}
    assert safe_get_str(data, "page-group", strip_id=False) == "Administration # 52840988022029242"


def test_safe_get_int():
    data = {"id": 42}
    assert safe_get_int(data, "id") == 42
    assert safe_get_int(data, "missing", 0) == 0


def test_safe_get_bool():
    data = {"edit": {"enabled": True}}
    assert safe_get_bool(data, "edit.enabled") is True
    assert safe_get_bool(data, "edit.missing") is False


def test_safe_get_list():
    data = {"ops": ["Add", "Delete"]}
    assert safe_get_list(data, "ops") == ["Add", "Delete"]
    assert safe_get_list(data, "missing") == []


def test_strip_apex_id():
    assert strip_apex_id("Foo # 123456789") == "Foo"
    assert strip_apex_id("Foo") == "Foo"
    assert strip_apex_id(None) is None


def test_collect_build_options():
    """Zbiera wszystkie build-option z zagnieżdżonej struktury."""
    data = {
        "build-option": "Feature: X # 123",
        "regions": [
            {"build-option": "Commented Out # 456"},
            {"nested": {"build-option": "Feature: Y # 789"}},
        ],
    }
    result = collect_build_options(data)
    assert "Feature: X" in result
    assert "Commented Out" in result
    assert "Feature: Y" in result
