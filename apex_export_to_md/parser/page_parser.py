"""Parser stron APEX (pages/*.yaml).

Czyta pliki YAML i konwertuje je na obiekty ApexPage z pełną strukturą:
regiony, kolumny, elementy, przyciski, procesy, DA, branches, walidacje.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

import yaml

from apex_export_to_md.models import (
    ApexPage, Region, Column, PageItem, Process,
    DynamicAction, DynamicActionStep, Button, Branch, Validation,
)
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_int, safe_get_bool, safe_get_list,
    collect_build_options, clean_raw_attributes,
)

logger = logging.getLogger(__name__)


def parse_all_pages(pages_dir: Path) -> list[ApexPage]:
    """Parsuj wszystkie pliki stron z katalogu pages/.

    Args:
        pages_dir: Ścieżka do katalogu pages/

    Returns:
        Lista sparsowanych stron, posortowana po ID
    """
    pages: list[ApexPage] = []
    if not pages_dir.exists():
        logger.warning("Katalog stron nie istnieje: %s", pages_dir)
        return pages

    for yaml_file in sorted(pages_dir.glob("p*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                page = parse_page(data)
                pages.append(page)
                logger.debug("Sparsowano stronę: %s (ID=%d)", page.name, page.id)
        except Exception as e:
            logger.warning("Błąd parsowania %s: %s", yaml_file.name, e)

    return sorted(pages, key=lambda p: p.id)


def parse_page(data: dict) -> ApexPage:
    """Parsuj pojedynczą stronę APEX z danych YAML.

    Args:
        data: Słownik z załadowanego pliku YAML strony

    Returns:
        Obiekt ApexPage z wypełnionymi polami
    """
    ident = data.get("identification", {})

    # Parsowanie page-group — może być w identification lub na poziomie top-level
    page_group = safe_get_str(ident, "page-group", strip_id=True)

    page_skip = {"id", "regions", "page-items", "buttons", "processes",
                 "dynamic-actions", "branches", "validations", "css", "javascript"}

    return ApexPage(
        id=safe_get_int(data, "id"),
        name=safe_get_str(ident, "name", "") or "",
        alias=safe_get_str(ident, "alias", "") or "",
        title=safe_get_str(ident, "title", "") or "",
        page_group=page_group,
        page_mode=safe_get_str(data, "appearance.page-mode", "Normal") or "Normal",
        security=data.get("security", {}),
        build_options=collect_build_options(data),
        regions=_parse_regions(data.get("regions", [])),
        items=_parse_items(data.get("page-items", [])),
        buttons=_parse_buttons(data.get("buttons", [])),
        processes=_parse_processes(data.get("processes", [])),
        dynamic_actions=_parse_dynamic_actions(data.get("dynamic-actions", [])),
        branches=_parse_branches(data.get("branches", [])),
        validations=_parse_validations(data.get("validations", [])),
        css_inline=safe_get(data, "css.inline"),
        js_inline=(
            safe_get(data, "javascript.execute-when-page-loads")
            or safe_get(data, "javascript.inline")
        ),
        raw_attributes=clean_raw_attributes(data, page_skip),
    )


# --- Parsery podrzędne ---


def _parse_regions(regions_data: list[dict]) -> list[Region]:
    """Parsuj listę regionów."""
    regions: list[Region] = []
    region_skip = {"id", "identification", "source", "layout", "attributes",
                   "columns"}
    for r in regions_data or []:
        ident = r.get("identification", {})
        source = r.get("source", {})
        attrs = r.get("attributes", {})
        edit = attrs.get("edit", {})

        region = Region(
            name=safe_get_str(ident, "name", "") or "",
            title=safe_get_str(ident, "title"),
            type=safe_get_str(ident, "type", "") or "",
            source_table=safe_get_str(source, "table-name"),
            source_sql=safe_get(source, "sql-query"),
            parent_region=_clean_parent_region(safe_get_str(r, "layout.parent-region")),
            columns=_parse_columns(r.get("columns", [])),
            editable=safe_get_bool(edit, "enabled") if isinstance(edit, dict) else False,
            allowed_operations=safe_get_list(edit, "allowed-operations") if isinstance(edit, dict) else [],
            raw_attributes=clean_raw_attributes(r, region_skip),
        )
        regions.append(region)
    return regions


def _clean_parent_region(value: str | None) -> str | None:
    """Zamień 'No Parent' na None."""
    if value and value.strip().lower() == "no parent":
        return None
    return value


def _parse_columns(columns_data: list[dict]) -> list[Column]:
    """Parsuj listę kolumn regionu."""
    columns: list[Column] = []
    col_skip = {"id", "identification", "source", "link", "heading"}
    for c in columns_data or []:
        ident = c.get("identification", {})
        source = c.get("source", {})
        link = c.get("link", {})
        link_target_raw = safe_get(link, "target.page")

        link_target = None
        if link_target_raw:
            link_str = str(link_target_raw).split("#")[0].strip()
            try:
                link_target = str(int(link_str))
            except ValueError:
                link_target = link_str

        column = Column(
            name=safe_get_str(ident, "column-name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            heading=safe_get_str(c, "heading.heading"),
            source_column=safe_get_str(source, "database-column"),
            data_type=safe_get_str(source, "data-type"),
            link_target=link_target,
            lov=safe_get_str(c, "list-of-values.list-of-values", strip_id=True),
            primary_key=safe_get_bool(source, "primary-key"),
            raw_attributes=clean_raw_attributes(c, col_skip),
        )
        columns.append(column)
    return columns


def _parse_items(items_data: list[dict]) -> list[PageItem]:
    """Parsuj elementy formularza strony."""
    items: list[PageItem] = []
    item_skip = {"id", "identification", "label"}
    for item_data in items_data or []:
        ident = item_data.get("identification", {})
        source = item_data.get("source", {})

        source_type = safe_get_str(source, "type", "")
        source_column = None
        if source_type and "database" in source_type.lower():
            source_column = safe_get_str(source, "database-column")

        item = PageItem(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            label=safe_get_str(item_data, "label.label"),
            source_column=source_column,
            lov=safe_get_str(item_data, "list-of-values.list-of-values", strip_id=True),
            default_value=safe_get_str(item_data, "default.static-value"),
            raw_attributes=clean_raw_attributes(item_data, item_skip),
        )
        items.append(item)
    return items


def _parse_buttons(buttons_data: list[dict]) -> list[Button]:
    """Parsuj przyciski strony."""
    buttons: list[Button] = []
    btn_skip = {"id", "identification", "behavior"}
    for b in buttons_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})

        target_page = None
        target = behavior.get("target")
        if isinstance(target, dict):
            page_raw = target.get("page")
            if page_raw:
                try:
                    target_page = int(str(page_raw).split("#")[0].strip())
                except ValueError:
                    pass

        button = Button(
            name=safe_get_str(ident, "button-name", "") or "",
            label=safe_get_str(b, "label.label"),
            action=safe_get_str(behavior, "action") if isinstance(behavior, dict) else None,
            target_page=target_page,
            is_hot=safe_get_bool(b, "appearance.hot"),
            raw_attributes=clean_raw_attributes(b, btn_skip),
        )
        buttons.append(button)
    return buttons


def _parse_processes(processes_data: list[dict]) -> list[Process]:
    """Parsuj procesy strony."""
    processes: list[Process] = []
    proc_skip = {"id", "identification", "source", "server-side-condition"}
    for p in processes_data or []:
        ident = p.get("identification", {})
        source = p.get("source", {})
        proc_type = safe_get_str(ident, "type", "") or ""

        code = (
            safe_get(source, "pl/sql-code")
            or safe_get(source, "javascript-code")
        )

        if not code and "invoke" in proc_type.lower():
            settings = p.get("settings", {})
            pkg = safe_get_str(settings, "package")
            proc = safe_get_str(settings, "procedure-or-function")
            if pkg or proc:
                code = f"INVOKE: {pkg or '?'}.{proc or '?'}"

        ssc = p.get("server-side-condition", {})
        condition = None
        btn_pressed = None
        if isinstance(ssc, dict):
            btn_pressed = safe_get_str(ssc, "when-button-pressed", strip_id=True)
            cond_parts = []
            for key in ("type", "value", "expression"):
                val = ssc.get(key)
                if val:
                    cond_parts.append(f"{key}={val}")
            if cond_parts:
                condition = ", ".join(cond_parts)

        process = Process(
            name=safe_get_str(ident, "name", "") or "",
            type=proc_type,
            language=safe_get_str(source, "language"),
            point=safe_get_str(p, "execution.point", "") or "",
            code=code,
            condition=condition,
            when_button_pressed=btn_pressed,
            raw_attributes=clean_raw_attributes(p, proc_skip),
        )
        processes.append(process)
    return processes


def _parse_dynamic_actions(da_data: list[dict]) -> list[DynamicAction]:
    """Parsuj akcje dynamiczne z listą kroków."""
    dynamic_actions: list[DynamicAction] = []
    da_skip = {"id", "identification", "when", "actions"}
    for da in da_data or []:
        ident = da.get("identification", {})
        when = da.get("when", {})

        trigger = (
            safe_get(when, "item")
            or safe_get(when, "jquery-selector")
            or safe_get(when, "region")
            or safe_get(when, "button")
        )

        action = DynamicAction(
            name=safe_get_str(ident, "name", "") or "",
            event=safe_get_str(when, "event", "") or "",
            selection_type=safe_get_str(when, "selection-type"),
            trigger_selector=trigger,
            event_scope=safe_get_str(da, "execution.event-scope"),
            static_container=safe_get(da, "execution.static-container-(jquery-selector)"),
            actions=_parse_da_steps(da.get("actions", [])),
            raw_attributes=clean_raw_attributes(da, da_skip),
        )
        dynamic_actions.append(action)
    return dynamic_actions


def _parse_da_steps(steps_data: list[dict]) -> list[DynamicActionStep]:
    """Parsuj kroki akcji dynamicznej."""
    steps: list[DynamicActionStep] = []
    step_skip = {"id", "identification", "settings", "affected-elements"}
    for s in steps_data or []:
        ident = s.get("identification", {})
        settings = s.get("settings", {})
        affected = s.get("affected-elements", {})

        code = (
            safe_get(settings, "pl/sql-code")
            or safe_get(settings, "javascript-code")
        )

        ae_type = safe_get_str(affected, "selection-type") if isinstance(affected, dict) else None
        ae_selector = (
            safe_get(affected, "jquery-selector")
            or safe_get(affected, "item")
            or safe_get(affected, "region")
        ) if isinstance(affected, dict) else None

        affected_str = None
        if ae_type and ae_selector:
            affected_str = f"{ae_type}: {ae_selector}"
        elif ae_selector:
            affected_str = str(ae_selector)

        step = DynamicActionStep(
            type=safe_get_str(ident, "action", "") or "",
            code=code,
            affected_elements=affected_str,
            fire_on_initialization=safe_get_bool(s, "execution.fire-on-initialization"),
            raw_attributes=clean_raw_attributes(s, step_skip),
        )
        steps.append(step)
    return steps


def _parse_branches(branches_data: list[dict]) -> list[Branch]:
    """Parsuj rozgałęzienia nawigacyjne."""
    branches: list[Branch] = []
    branch_skip = {"id", "identification", "behavior", "server-side-condition"}
    for b in branches_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})
        target = behavior.get("target", {}) if isinstance(behavior, dict) else {}

        target_page = None
        page_raw = safe_get(target, "page") if isinstance(target, dict) else None
        if page_raw:
            try:
                target_page = int(str(page_raw).split("#")[0].strip())
            except ValueError:
                pass

        ssc = b.get("server-side-condition", {})
        condition = None
        if isinstance(ssc, dict) and ssc:
            cond_parts = []
            for key in ("type", "value", "expression"):
                val = ssc.get(key)
                if val:
                    cond_parts.append(f"{key}={val}")
            if cond_parts:
                condition = ", ".join(cond_parts)

        branch = Branch(
            name=safe_get_str(ident, "name"),
            type=safe_get_str(behavior, "type", "") or "" if isinstance(behavior, dict) else "",
            target_page=target_page,
            target_url=safe_get(target, "url") if isinstance(target, dict) else None,
            point=safe_get_str(b, "execution.point", "") or "",
            condition=condition,
            raw_attributes=clean_raw_attributes(b, branch_skip),
        )
        branches.append(branch)
    return branches


def _parse_validations(validations_data: list[dict]) -> list[Validation]:
    """Parsuj walidacje strony."""
    validations: list[Validation] = []
    val_skip = {"id", "identification", "validation", "server-side-condition"}
    for v in validations_data or []:
        ident = v.get("identification", {})
        val_block = v.get("validation", {})

        ssc = v.get("server-side-condition", {})
        condition = None
        if isinstance(ssc, dict) and ssc:
            cond_parts = [f"{k}={v_}" for k, v_ in ssc.items() if v_]
            if cond_parts:
                condition = ", ".join(cond_parts)

        validation = Validation(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(val_block, "type", "") or "",
            code=safe_get(val_block, "pl/sql-function-body"),
            condition=condition,
            raw_attributes=clean_raw_attributes(v, val_skip),
        )
        validations.append(validation)
    return validations
