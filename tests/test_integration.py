"""Test integracyjny — uruchomienie pełnego pipeline'u na prawdziwych danych projektu.

Testy są pomijane automatycznie, jeśli katalog z danymi APEX nie istnieje.
Ścieżkę można nadpisać zmienną środowiskową APEX_EXPORT_DIR.
"""
import os
from pathlib import Path
import pytest

from apex_export_to_md.config import AppConfig
from apex_export_to_md.cli import run_pipeline


# Ścieżka do prawdziwych danych — pomiń test jeśli brak
REAL_DATA_DIR = Path(os.environ.get(
    "APEX_EXPORT_DIR",
    "c:/_projekty/SKW_TO_APEX/program/readable/application",
))


@pytest.mark.skipif(
    not REAL_DATA_DIR.exists(),
    reason=f"Brak danych testowych: {REAL_DATA_DIR}",
)
class TestIntegration:

    def test_pipeline_oba_formaty(self, tmp_path):
        """Pipeline generuje oba pliki bez błędów i z odpowiednią zawartością."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_prefix="test_export",
            output_format="both",
        )
        run_pipeline(config)

        human_file = tmp_path / "test_export_human.md"
        llm_file = tmp_path / "test_export_llm.md"

        # Oba pliki powinny istnieć
        assert human_file.exists(), "Brak pliku human.md"
        assert llm_file.exists(), "Brak pliku llm.md"

        human_content = human_file.read_text(encoding="utf-8")
        llm_content = llm_file.read_text(encoding="utf-8")

        # Minimalny rozmiar — obie wersje powinny mieć treść
        assert len(human_content) > 500, f"Plik human za mały: {len(human_content)} znaków"
        assert len(llm_content) > 200, f"Plik llm za mały: {len(llm_content)} znaków"

        # LLM powinien być mniejszy niż human (bardziej skondensowany)
        assert len(llm_content) < len(human_content), (
            f"Plik llm ({len(llm_content)}) powinien być mniejszy niż human ({len(human_content)})"
        )

    def test_pipeline_filtruje_strony_admin(self, tmp_path):
        """Pipeline w trybie auto pomija strony administracyjne APEX.

        Sprawdzamy, że strony admin nie pojawiają się jako NAGŁÓWKI STRON
        (format: '### Strona N: <nazwa>') — mogą jednak pojawić się
        w nawigacji lub build options jako referencje.
        """
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="human",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_human.md").read_text(encoding="utf-8")

        # Strony użytkownika DAW_* powinny być obecne jako nagłówki stron
        assert "DAW_LISTA_AUDYTOW" in content or "DAW_ANKIETA" in content, (
            "Brak stron użytkownika DAW_* w wyjściu"
        )

        # Strony administracyjne NIE powinny pojawić się jako nagłówki stron
        # (format nagłówka strony: "### Strona N: <nazwa>")
        assert "### Strona" not in content or all(
            admin not in line
            for line in content.split("\n")
            if line.startswith("### Strona")
            for admin in ("Activity Dashboard", "Configuration Options", "Manage User Access")
        ), "Strony administracyjne nie powinny być dołączone jako strony w wyjściu"

    def test_pipeline_zawiera_shared_components(self, tmp_path):
        """Pipeline dołącza LOV-y i schematy autoryzacji ze shared components."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="human",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_human.md").read_text(encoding="utf-8")

        # Sekcja LOV powinna być obecna
        assert "LOV" in content or "Lista wartości" in content, (
            "Brak sekcji LOV w wyjściu"
        )

        # Sekcja autoryzacji powinna być obecna
        assert "autoryzacj" in content.lower() or "AUTH" in content, (
            "Brak sekcji autoryzacji w wyjściu"
        )

    def test_pipeline_tryb_all(self, tmp_path):
        """Pipeline w trybie 'all' zawiera wszystkie strony, włącznie z administracyjnymi."""
        config = AppConfig(
            input_dir=str(REAL_DATA_DIR),
            output_dir=str(tmp_path),
            output_format="llm",
            page_filter="all",
        )
        run_pipeline(config)

        content = (tmp_path / "apex_export_llm.md").read_text(encoding="utf-8")

        # Strony administracyjne powinny być obecne w trybie all
        assert "Administration" in content or "Global Page" in content, (
            "Tryb 'all' powinien zawierać strony administracyjne"
        )
