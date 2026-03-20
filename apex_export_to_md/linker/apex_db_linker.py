"""Automatyczne wykrywanie powiązań między stronami APEX a obiektami DB.

Heurystyki: parsowanie SQL z regionów, procesów, walidacji i LOV-ów.
Dopasowanie z word boundaries, case-insensitive, longest-first.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from apex_export_to_md.models.apex_models import ApexApp, ApexPage
from apex_export_to_md.models.db_models import DbSchema


@dataclass
class ApexDbLink:
    """Powiązanie między elementem APEX a obiektami bazy danych."""
    page_id: int
    page_name: str
    db_objects: list[str] = field(default_factory=list)
    source_type: str = ""     # "region", "process", "validation", "lov"
    source_name: str = ""     # nazwa regionu/procesu/LOV


class ApexDbLinker:
    """Wykrywa powiązania APEX↔DB przez heurystyki SQL."""

    def __init__(self, app: ApexApp, schema: DbSchema):
        self._app = app
        self._schema = schema
        # Zbierz nazwy obiektów DB, sortuj od najdłuższych
        self._db_names = sorted(
            [t.name for t in schema.tables] + [v.name for v in schema.views],
            key=lambda x: -len(x),
        )

    def find_links(self) -> list[ApexDbLink]:
        """Zwróć listę powiązań APEX↔DB."""
        links: list[ApexDbLink] = []

        for page in self._app.pages:
            links.extend(self._scan_page(page))

        # LOV-y (nie przypisane do strony — page_id=0)
        for lov in self._app.lovs:
            sql = lov.sql_query or ""
            if sql:
                objects = self._find_db_objects_in_sql(sql)
                if objects:
                    links.append(ApexDbLink(
                        page_id=0, page_name="(shared)",
                        db_objects=objects,
                        source_type="lov", source_name=lov.name,
                    ))

        return links

    def _scan_page(self, page: ApexPage) -> list[ApexDbLink]:
        links: list[ApexDbLink] = []

        # Regiony
        for region in page.regions:
            objects: list[str] = []
            if region.source_table:
                # Bezpośrednia referencja do tabeli
                if region.source_table in self._db_names:
                    objects.append(region.source_table)
            if region.source_sql:
                objects.extend(self._find_db_objects_in_sql(region.source_sql))
            # Deduplikacja z zachowaniem kolejności
            objects = list(dict.fromkeys(objects))
            if objects:
                links.append(ApexDbLink(
                    page_id=page.id, page_name=page.name,
                    db_objects=objects,
                    source_type="region", source_name=region.name,
                ))

        # Procesy
        for proc in page.processes:
            if proc.code:
                objects = self._find_db_objects_in_sql(proc.code)
                if objects:
                    links.append(ApexDbLink(
                        page_id=page.id, page_name=page.name,
                        db_objects=objects,
                        source_type="process", source_name=proc.name,
                    ))

        # Walidacje
        for val in page.validations:
            if val.code:
                objects = self._find_db_objects_in_sql(val.code)
                if objects:
                    links.append(ApexDbLink(
                        page_id=page.id, page_name=page.name,
                        db_objects=objects,
                        source_type="validation", source_name=val.name,
                    ))

        return links

    def _find_db_objects_in_sql(self, sql: str) -> list[str]:
        """Szukaj nazw tabel/widoków w tekście SQL.

        Word boundaries + case-insensitive + longest-first.
        """
        found: list[str] = []
        sql_upper = sql.upper()

        for name in self._db_names:
            pattern = r'(?<![A-Z0-9_])' + re.escape(name) + r'(?![A-Z0-9_])'
            if re.search(pattern, sql_upper):
                found.append(name)

        return found
