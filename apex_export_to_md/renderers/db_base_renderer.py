# apex_export_to_md/renderers/db_base_renderer.py
"""Abstrakcyjna klasa bazowa rendererów bazy danych.

Analogiczna do BaseRenderer, ale operuje na DbSchema.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from apex_export_to_md.models.db_models import DbSchema
from apex_export_to_md.config import AppConfig


class DbBaseRenderer(ABC):
    """Bazowy renderer DB — generuje tekst z modelu DbSchema."""

    def __init__(self, config: AppConfig):
        self._config = config

    @abstractmethod
    def render(self, schema: DbSchema) -> str:
        """Generuj tekst z modelu bazy danych."""
        ...

    def _should_include_code(self) -> bool:
        return self._config.include_code == "full"

    def _should_summarize_code(self) -> bool:
        return self._config.include_code == "summary"
