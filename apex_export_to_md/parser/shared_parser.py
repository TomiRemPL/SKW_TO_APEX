"""Parser shared components (LOVs, autoryzacje, listy, breadcrumbs, itp.).

Czyta pliki YAML z katalogu shared_components/ i konwertuje na modele.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

import yaml

from apex_export_to_md.models import (
    LOV, Authorization, NavList, AppItem, BuildOption, Breadcrumb, AclRole,
    Authentication, Plugin, SearchConfig, DataLoadDef, StaticFile, PageGroup,
)
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_bool, sanitize_yaml_text, strip_apex_id,
)

logger = logging.getLogger(__name__)


def load_yaml_file(path: Path) -> Any:
    """Bezpieczne wczytanie pliku YAML."""
    if not path.exists():
        logger.debug("Plik nie istnieje, pomijam: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(sanitize_yaml_text(f.read()))
    except Exception as e:
        logger.warning("Błąd wczytywania %s: %s", path.name, e)
        return None


def parse_app_definition(data: dict) -> tuple[str, str, str]:
    """Wyciągnij nazwę, ID i alias aplikacji z f*.yaml.

    Returns:
        Tuple (name, id, alias)
    """
    ident = data.get("identification", {})
    return (
        safe_get_str(ident, "name", "") or "",
        str(data.get("id", "")),
        safe_get_str(ident, "alias", "") or "",
    )


def parse_lovs(data: list[dict] | None) -> list[LOV]:
    """Parsuj listy wartości (LOV) — trzy typy: Table, SQL Query, Static Values."""
    if not data:
        return []
    lovs: list[LOV] = []
    for item in data:
        ident = item.get("identification", {})
        source = item.get("source", {})
        source_type = safe_get_str(source, "type", "") or ""
        col_mapping = item.get("column-mapping", {})

        # Dla Static Values — wyciągnij wpisy
        entries = None
        if "static" in source_type.lower():
            raw_entries = item.get("entries", [])
            entries = []
            for e in raw_entries:
                entry_data = e.get("entry", e)
                entries.append({
                    "display": entry_data.get("display", ""),
                    "return": entry_data.get("return", ""),
                })

        lov = LOV(
            name=safe_get_str(ident, "name", "") or "",
            source_type=source_type,
            source_table=safe_get_str(source, "table-name"),
            sql_query=safe_get(source, "sql-query"),
            entries=entries,
            return_column=safe_get_str(col_mapping, "return"),
            display_column=safe_get_str(col_mapping, "display"),
        )
        lovs.append(lov)
    return lovs


def parse_authorizations(data: list[dict] | None) -> list[Authorization]:
    """Parsuj schematy autoryzacji."""
    if not data:
        return []
    auths: list[Authorization] = []
    for item in data:
        ident = item.get("identification", {})
        scheme = item.get("authorization-scheme", {})
        settings = item.get("settings", {})

        auth = Authorization(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(scheme, "type"),
            code=safe_get(settings, "pl/sql-function-body"),
            role_or_group=safe_get(settings, "name(s)"),
        )
        auths.append(auth)
    return auths


def parse_nav_lists(data: list[dict] | None) -> list[NavList]:
    """Parsuj listy nawigacyjne."""
    if not data:
        return []
    nav_lists: list[NavList] = []
    for item in data:
        ident = item.get("identification", {})
        raw_entries = item.get("entries", [])
        entries: list[dict] = []
        for e in raw_entries:
            label_block = e.get("label", {})
            link = e.get("link", {})
            target = link.get("target", {}) if isinstance(link, dict) else {}
            entries.append({
                "label": safe_get_str(label_block, "label") if isinstance(label_block, dict) else None,
                "target_page": safe_get(target, "page") if isinstance(target, dict) else None,
                "parent": safe_get_str(e.get("identification", {}), "parent-entry", strip_id=True),
            })
        nav_list = NavList(
            name=safe_get_str(ident, "name", "") or "",
            entries=entries,
        )
        nav_lists.append(nav_list)
    return nav_lists


def parse_app_items(data: list[dict] | None) -> list[AppItem]:
    """Parsuj zmienne globalne aplikacji."""
    if not data:
        return []
    items: list[AppItem] = []
    for item in data:
        ident = item.get("identification", {})
        items.append(AppItem(
            name=safe_get_str(ident, "name", "") or "",
            scope=safe_get_str(ident, "scope"),
        ))
    return items


def parse_build_options(data: list[dict] | None) -> list[BuildOption]:
    """Parsuj opcje budowania (feature toggles)."""
    if not data:
        return []
    options: list[BuildOption] = []
    for item in data:
        ident = item.get("identification", {})
        status_block = item.get("status", {})
        options.append(BuildOption(
            name=safe_get_str(ident, "name", "") or "",
            status=safe_get_str(status_block, "status", "") or "",
        ))
    return options


def parse_breadcrumbs(data: list[dict] | None) -> list[Breadcrumb]:
    """Parsuj ścieżki nawigacyjne."""
    if not data:
        return []
    breadcrumbs: list[Breadcrumb] = []
    for item in data:
        ident = item.get("identification", {})
        raw_entries = item.get("entries", [])
        entries: list[dict] = []
        for e in raw_entries:
            e_ident = e.get("identification", {})
            link = e.get("link", {})
            target = link.get("target", {}) if isinstance(link, dict) else {}
            entries.append({
                "name": safe_get_str(e_ident, "name"),
                "page_number": safe_get(e_ident, "page-number"),
                "target_page": safe_get(target, "page"),
            })
        breadcrumbs.append(Breadcrumb(
            name=safe_get_str(ident, "name", "") or "",
            entries=entries,
        ))
    return breadcrumbs


def parse_acl_roles(data: list[dict] | None) -> list[AclRole]:
    """Parsuj role ACL."""
    if not data:
        return []
    roles: list[AclRole] = []
    for item in data:
        ident = item.get("identification", {})
        roles.append(AclRole(
            name=safe_get_str(ident, "name", "") or "",
            static_id=safe_get_str(item, "advanced.static-id"),
        ))
    return roles


def parse_authentications(data: list[dict] | None) -> list[Authentication]:
    """Parsuj schematy autentykacji (LDAP, OpenID/ADFS, APEX Accounts)."""
    if not data:
        return []
    auths: list[Authentication] = []
    for item in data:
        ident = item.get("identification", {})
        settings = item.get("settings", {})
        session_not_valid = item.get("session-not-valid", {})
        login_processing = item.get("login-processing", {})

        # port może być liczbą lub stringiem — trzymaj jako string
        port = safe_get(settings, "port")
        port_str = str(port) if port is not None else None

        auths.append(Authentication(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(settings, "type"),
            host=safe_get_str(settings, "host"),
            port=port_str,
            use_ssl=safe_get_str(settings, "use-ssl"),
            dn_string=safe_get_str(settings, "distinguished-name-(dn)-string"),
            session_not_valid_redirect=safe_get_str(session_not_valid, "redirect-to")
            if isinstance(session_not_valid, dict) else None,
            switch_in_session=safe_get_bool(login_processing, "switch-in-session")
            if isinstance(login_processing, dict) else None,
        ))
    return auths


def parse_plugins(data: list[dict] | None) -> list[Plugin]:
    """Parsuj pluginy APEX (template components, item types, DA types)."""
    if not data:
        return []
    plugins: list[Plugin] = []
    for item in data:
        ident = item.get("identification", {})
        templates = item.get("templates", {})
        available_as: list[str] = []
        if isinstance(templates, dict):
            raw = templates.get("available-as")
            if isinstance(raw, list):
                available_as = [str(a) for a in raw if a]
        plugins.append(Plugin(
            name=safe_get_str(ident, "name", "") or "",
            internal_name=safe_get_str(ident, "internal-name"),
            theme=safe_get_str(ident, "theme", strip_id=True),
            plugin_type=safe_get_str(ident, "type"),
            available_as=available_as,
        ))
    return plugins


def parse_search_configs(data: list[dict] | None) -> list[SearchConfig]:
    """Parsuj konfiguracje wyszukiwania aplikacji (App Search)."""
    if not data:
        return []
    configs: list[SearchConfig] = []
    for item in data:
        ident = item.get("identification", {})
        source = item.get("source", {})
        column_mapping = item.get("column-mapping", {})
        configs.append(SearchConfig(
            name=safe_get_str(ident, "name", "") or "",
            search_type=safe_get_str(source, "search-type"),
            location=safe_get_str(source, "location"),
            sql_query=safe_get(source, "sql-query"),
            searchable_columns=safe_get_str(source, "searchable-columns"),
            column_mapping=column_mapping if isinstance(column_mapping, dict) else {},
        ))
    return configs


def parse_data_load_defs(data: list[dict] | None) -> list[DataLoadDef]:
    """Parsuj definicje ładowania danych (Data Load Definitions)."""
    if not data:
        return []
    defs: list[DataLoadDef] = []
    for item in data:
        ident = item.get("identification", {})
        target = item.get("target", {})
        advanced = item.get("advanced", {})
        defs.append(DataLoadDef(
            name=safe_get_str(ident, "name", "") or "",
            target_type=safe_get_str(target, "type") if isinstance(target, dict) else None,
            table_name=safe_get_str(target, "table-name") if isinstance(target, dict) else None,
            loading_method=safe_get_str(target, "loading-method") if isinstance(target, dict) else None,
            commit_interval=str(safe_get(advanced, "commit-interval"))
            if safe_get(advanced, "commit-interval") is not None else None,
            static_id=safe_get_str(item, "advanced.static-id"),
        ))
    return defs


def parse_static_files(data: list[dict] | None) -> list[StaticFile]:
    """Parsuj pliki statyczne aplikacji (Static Application Files)."""
    if not data:
        return []
    files: list[StaticFile] = []
    for item in data:
        ident = item.get("identification", {})
        attrs = item.get("attributes", {})
        files.append(StaticFile(
            file_name=safe_get_str(ident, "file-name", "") or "",
            mime_type=safe_get_str(attrs, "mime-type") if isinstance(attrs, dict) else None,
        ))
    return files


def parse_page_groups(data: list[dict] | None) -> list[PageGroup]:
    """Parsuj grupy stron aplikacji."""
    if not data:
        return []
    groups: list[PageGroup] = []
    for item in data:
        ident = item.get("identification", {})
        groups.append(PageGroup(
            name=safe_get_str(ident, "name", "") or "",
        ))
    return groups


def parse_shared_components(shared_dir: Path) -> dict:
    """Parsuj wszystkie shared components z katalogu.

    Returns:
        Słownik z kluczami: lovs, authorizations, nav_lists,
        app_items, build_options, breadcrumbs, acl_roles
    """
    result = {
        "lovs": [],
        "authorizations": [],
        "nav_lists": [],
        "app_items": [],
        "build_options": [],
        "breadcrumbs": [],
        "acl_roles": [],
        "authentications": [],
        "plugins": [],
        "search_configs": [],
        "data_load_defs": [],
        "static_files": [],
        "page_groups": [],
    }

    if not shared_dir.exists():
        logger.warning("Katalog shared_components nie istnieje: %s", shared_dir)
        return result

    # Mapowanie: nazwa pliku → (funkcja parsująca, klucz wyniku)
    parsers = {
        "lovs.yaml": (parse_lovs, "lovs"),
        "authorizations.yaml": (parse_authorizations, "authorizations"),
        "lists.yaml": (parse_nav_lists, "nav_lists"),
        "app_items.yaml": (parse_app_items, "app_items"),
        "build_options.yaml": (parse_build_options, "build_options"),
        "breadcrumbs.yaml": (parse_breadcrumbs, "breadcrumbs"),
        "acl_roles.yaml": (parse_acl_roles, "acl_roles"),
        "authentications.yaml": (parse_authentications, "authentications"),
        "plugins.yaml": (parse_plugins, "plugins"),
        "search_configs.yaml": (parse_search_configs, "search_configs"),
        "data_load_definitions.yaml": (parse_data_load_defs, "data_load_defs"),
        "app_static_files.yaml": (parse_static_files, "static_files"),
    }

    for filename, (parser_fn, result_key) in parsers.items():
        data = load_yaml_file(shared_dir / filename)
        if data:
            result[result_key] = parser_fn(data)
            logger.debug("Sparsowano %s: %d elementów", filename, len(result[result_key]))

    # page_groups.yaml leży jeden poziom wyżej (w application/), nie w shared_components/
    app_dir = shared_dir.parent
    page_groups_data = load_yaml_file(app_dir / "page_groups.yaml")
    if page_groups_data:
        result["page_groups"] = parse_page_groups(page_groups_data)
        logger.debug("Sparsowano page_groups.yaml: %d elementów", len(result["page_groups"]))

    return result
