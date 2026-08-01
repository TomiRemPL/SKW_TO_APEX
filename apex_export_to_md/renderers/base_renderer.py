"""Abstrakcyjna klasa bazowa rendererów.

Definiuje interfejs wspólny dla wszystkich formatów wyjściowych.
Nowe renderery (np. JSON, HTML) powinny dziedziczyć po BaseRenderer.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from apex_export_to_md.models import ApexApp
from apex_export_to_md.config import AppConfig


class BaseRenderer(ABC):
    """Bazowy renderer — generuje tekst z modelu ApexApp."""

    def __init__(self, config: AppConfig, timestamp: str = ""):
        self._config = config
        self._timestamp = timestamp

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
