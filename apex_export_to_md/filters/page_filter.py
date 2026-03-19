"""Filtr stron APEX — heurystyki do rozróżnienia stron użytkownika od standardowych.

Tryby filtrowania:
  - auto: heurystyki (page-group, authorization-scheme, nazwa systemowa)
  - all: brak filtrowania
  - prefix:<X>: filtr po prefiksie nazwy strony
  - ids:<1,2,3>: filtr po konkretnych ID stron
"""
from __future__ import annotations
import logging
from apex_export_to_md.config import (
    AppConfig, STANDARD_PAGE_GROUPS, STANDARD_AUTH_SCHEME, SYSTEM_PAGE_NAMES,
)
from apex_export_to_md.models import ApexPage
from apex_export_to_md.parser.yaml_helpers import strip_apex_id

logger = logging.getLogger(__name__)


class PageFilter:
    """Filtruje strony APEX zgodnie z konfiguracją."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._mode, self._param = self._parse_filter_spec(config.page_filter)

    @staticmethod
    def _parse_filter_spec(spec: str) -> tuple[str, str]:
        """Parsuj specyfikację filtra, np. 'prefix:DAW_' → ('prefix', 'DAW_')."""
        if ":" in spec:
            mode, param = spec.split(":", 1)
            return mode.strip(), param.strip()
        return spec.strip(), ""

    def filter_pages(self, pages: list[ApexPage]) -> list[ApexPage]:
        """Filtruj listę stron zgodnie z konfiguracją.

        Returns:
            Lista stron spełniających kryteria filtra
        """
        extra_ids = set(self._config.extra_pages)

        if self._mode == "all":
            return list(pages)

        elif self._mode == "prefix":
            prefix = self._param
            return [
                p for p in pages
                if p.name.startswith(prefix) or p.id in extra_ids
            ]

        elif self._mode == "ids":
            allowed_ids = set()
            for part in self._param.split(","):
                part = part.strip()
                if part.isdigit():
                    allowed_ids.add(int(part))
            allowed_ids.update(extra_ids)
            return [p for p in pages if p.id in allowed_ids]

        else:
            # Tryb auto — heurystyki
            result: list[ApexPage] = []
            for page in pages:
                if page.id in extra_ids:
                    result.append(page)
                    continue
                if self._is_standard_page(page):
                    logger.debug("Pomijam stronę standardową: %s (ID=%d)", page.name, page.id)
                    continue
                result.append(page)
            return result

    def _is_standard_page(self, page: ApexPage) -> bool:
        """Sprawdź, czy strona jest standardową stroną APEX (do pominięcia).

        Heurystyki:
        1. page_group w STANDARD_PAGE_GROUPS
        2. authorization-scheme = STANDARD_AUTH_SCHEME
        3. name w SYSTEM_PAGE_NAMES
        """
        # Heurystyka 1: grupa stron
        if page.page_group and page.page_group in STANDARD_PAGE_GROUPS:
            return True

        # Heurystyka 2: schemat autoryzacji
        auth_scheme = page.security.get("authorization-scheme", "")
        if auth_scheme:
            clean_auth = strip_apex_id(str(auth_scheme)) or ""
            if clean_auth == STANDARD_AUTH_SCHEME:
                return True

        # Heurystyka 3: znane nazwy systemowe
        if page.name in SYSTEM_PAGE_NAMES:
            return True

        return False
