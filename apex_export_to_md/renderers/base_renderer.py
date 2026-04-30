"""Abstrakcyjna klasa bazowa rendererów.

Definiuje interfejs wspólny dla wszystkich formatów wyjściowych.
Nowe renderery (np. JSON, HTML) powinny dziedziczyć po BaseRenderer.
"""
from __future__ import annotations
import yaml
from abc import ABC, abstractmethod
from apex_export_to_md.models import ApexApp
from apex_export_to_md.config import AppConfig


class BaseRenderer(ABC):
    """Bazowy renderer — generuje tekst z modelu ApexApp."""

    def __init__(self, config: AppConfig):
        self._config = config

    @abstractmethod
    def render(self, app: ApexApp) -> str:
        """Generuj pełny tekst wyjściowy.

        Args:
            app: Model aplikacji APEX

        Returns:
            Tekst w docelowym formacie
        """
        ...

    def _should_include_code(self) -> bool:
        """Czy dołączyć pełny kod PL/SQL/JS."""
        return self._config.include_code == "full"

    def _should_summarize_code(self) -> bool:
        """Czy dołączyć skrócony kod (sygnatura + ...)."""
        return self._config.include_code == "summary"

    def _render_code_or_summary(self, code: str | None, lang: str = "sql") -> list[str]:
        """Renderuj kod w trybie full/summary/none.

        Returns:
            Lista linii z blokiem kodu, skrótem, lub pusta lista
        """
        if not code:
            return []
        if self._should_include_code():
            return [f"```{lang}", code, "```"]
        elif self._should_summarize_code():
            first_line = code.strip().split("\n")[0]
            return [f"> `{first_line}...`"]
        return []

    def _format_raw_attributes(self, raw_attrs: dict, indent: str = "  ") -> list[str]:
        """Formatuj raw_attributes jako czytelny blok YAML.

        Returns:
            Lista linii z sformatowanymi atrybutami, lub pusta lista
        """
        if not raw_attrs:
            return []
        lines: list[str] = []
        self._flatten_dict(raw_attrs, lines, indent)
        return lines

    def _flatten_dict(self, d: dict, lines: list[str], prefix: str = "") -> None:
        """Rekurencyjnie spłaszcz słownik do listy linii 'klucz: wartość'."""
        for key, value in d.items():
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_dict(value, lines, full_key + ".")
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    lines.append(f"{full_key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"{full_key}: [{len(value)} elementów]")
            else:
                lines.append(f"{full_key}: {value}")

    def _format_raw_yaml(self, raw_attrs: dict) -> str:
        """Formatuj raw_attributes jako blok YAML."""
        if not raw_attrs:
            return ""
        return yaml.dump(raw_attrs, allow_unicode=True, default_flow_style=False, sort_keys=False)
