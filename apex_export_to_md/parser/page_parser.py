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
    ApexPage, Region, Column, PageItem, Process, Computation,
    DynamicAction, DynamicActionStep, Button, Branch, Validation,
)
from apex_export_to_md.parser.yaml_helpers import (
    safe_get, safe_get_str, safe_get_int, safe_get_bool, safe_get_list,
    collect_build_options, sanitize_yaml_text, strip_apex_id,
)

logger = logging.getLogger(__name__)


def _compress_condition(ssc: Any) -> str | None:
    """Skondensuj blok server-side-condition do jednego stringa.

    Wzorzec zgodny z _parse_processes/_parse_branches: iteracja po kluczach
    (type, value, expression, item) plus when-button-pressed.
    """
    if not isinstance(ssc, dict) or not ssc:
        return None
    cond_parts: list[str] = []
    for key in ("type", "value", "expression", "item"):
        val = ssc.get(key)
        if val:
            cond_parts.append(f"{key}={val}")
    if cond_parts:
        return ", ".join(cond_parts)
    return None


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
                data = yaml.safe_load(sanitize_yaml_text(f.read()))
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

    # Wygląd strony: template + template-options
    appearance = data.get("appearance", {}) or {}
    page_template = (
        safe_get_str(appearance, "page-template", strip_id=True)
        or safe_get_str(appearance, "dialog-template", strip_id=True)
    )
    template_options_raw = safe_get_list(appearance, "template-options")
    template_options: list[str] = []
    for opt in template_options_raw:
        if isinstance(opt, str):
            template_options.append(strip_apex_id(opt) or opt)

    # Dialog — osobny blok top-level (chained, resizable, max-width...) dla stron modalnych
    dialog = data.get("dialog", {}) or {}
    if isinstance(dialog, dict):
        dialog = {k: v for k, v in dialog.items()}

    # Tekst pomocy strony
    help_text = safe_get_str(data, "help.help-text")

    # Navigation / Advanced / Session-management
    navigation = data.get("navigation", {}) or {}
    advanced = data.get("advanced", {}) or {}
    session_management = data.get("session-management", {}) or {}

    # Server cache (poziom strony)
    server_cache = safe_get_str(data, "server-cache.caching")

    # JavaScript: Function & Global Variable Declaration (pełny) + inline
    javascript_full = safe_get(data, "javascript.function-and-global-variable-declaration")
    js_inline = (
        safe_get(data, "javascript.execute-when-page-loads")
        or safe_get(data, "javascript.inline")
    )

    # Szczegóły security (poza authentication)
    security = data.get("security", {}) or {}
    security_detail: dict = {
        k: v for k, v in security.items() if k != "authentication"
    } if isinstance(security, dict) else {}

    return ApexPage(
        id=safe_get_int(data, "id"),
        name=safe_get_str(ident, "name", "") or "",
        alias=safe_get_str(ident, "alias", "") or "",
        title=safe_get_str(ident, "title", "") or "",
        page_group=page_group,
        page_mode=safe_get_str(data, "appearance.page-mode", "Normal") or "Normal",
        security=security,
        security_detail=security_detail,
        build_options=collect_build_options(data),
        regions=_parse_regions(data.get("regions", [])),
        items=_parse_items(data.get("page-items", [])),
        buttons=_parse_buttons(data.get("buttons", [])),
        processes=_parse_processes(data.get("processes", [])),
        dynamic_actions=_parse_dynamic_actions(data.get("dynamic-actions", [])),
        branches=_parse_branches(data.get("branches", [])),
        validations=_parse_validations(data.get("validations", [])),
        computations=_parse_computations(data.get("computations")),
        dialog=dialog,
        help_text=help_text,
        page_template=page_template,
        template_options=template_options,
        navigation=navigation,
        advanced=advanced,
        server_cache=server_cache,
        session_management=session_management,
        javascript_full=javascript_full,
        css_inline=safe_get(data, "css.inline"),
        js_inline=js_inline,
    )


# --- Parsery podrzędne ---


def _parse_regions(regions_data: list[dict]) -> list[Region]:
    """Parsuj listę regionów."""
    regions: list[Region] = []
    for r in regions_data or []:
        ident = r.get("identification", {})
        source = r.get("source", {})
        attrs = r.get("attributes", {})
        edit = attrs.get("edit", {})
        layout = r.get("layout", {})
        appearance = r.get("appearance", {})

        # template + template-options
        template = safe_get_str(appearance, "template", strip_id=True) if isinstance(appearance, dict) else None
        tpl_opts_raw = safe_get_list(appearance, "template-options") if isinstance(appearance, dict) else []
        template_options = [strip_apex_id(o) or o for o in tpl_opts_raw if isinstance(o, str)]

        # Skondensowany summary atrybutów (toolbar/download/heading/saved-reports/pagination)
        attributes_summary: dict = {}
        if isinstance(attrs, dict):
            for key in ("toolbar", "download", "heading", "saved-reports",
                        "performance", "appearance", "enable-users-to"):
                sub = attrs.get(key)
                if isinstance(sub, dict) and sub:
                    attributes_summary[key] = sub

        # Paginacja — skondensowana
        pagination = None
        pag = attrs.get("pagination") if isinstance(attrs, dict) else None
        if isinstance(pag, dict) and pag:
            parts = [f"{k}={v}" for k, v in pag.items() if v]
            if parts:
                pagination = ", ".join(parts)

        region = Region(
            name=safe_get_str(ident, "name", "") or "",
            title=safe_get_str(ident, "title"),
            type=safe_get_str(ident, "type", "") or "",
            source_table=safe_get_str(source, "table-name"),
            source_owner=safe_get_str(source, "table-owner"),
            source_sql=safe_get(source, "sql-query"),
            source_where=safe_get_str(source, "where-clause"),
            page_items_to_submit=safe_get_str(source, "page-items-to-submit"),
            parent_region=_clean_parent_region(safe_get_str(r, "layout.parent-region")),
            columns=_parse_columns(r.get("columns", [])),
            editable=safe_get_bool(edit, "enabled") if isinstance(edit, dict) else False,
            allowed_operations=safe_get_list(edit, "allowed-operations") if isinstance(edit, dict) else [],
            lost_update_type=safe_get_str(edit, "lost-update-type") if isinstance(edit, dict) else None,
            template=template,
            template_options=template_options,
            slot=safe_get_str(layout, "slot") if isinstance(layout, dict) else None,
            sequence=safe_get_int(layout, "sequence") if isinstance(layout, dict) else None,
            column_span=safe_get_str(layout, "column-span") if isinstance(layout, dict) else None,
            start_new_row=safe_get_bool(layout, "start-new-row") if isinstance(layout, dict) else None,
            order_by=safe_get_str(attrs, "order-by") if isinstance(attrs, dict) else None,
            source_location=safe_get_str(source, "location"),
            server_side_condition=_compress_condition(r.get("server-side-condition")),
            server_cache=safe_get_str(r, "server-cache.caching"),
            pagination=pagination,
            attributes_summary=attributes_summary,
            build_option=safe_get_str(r, "configuration.build-option", strip_id=True),
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
    for c in columns_data or []:
        ident = c.get("identification", {})
        source = c.get("source", {})
        link = c.get("link", {})
        link_target_raw = safe_get(link, "target.page")

        # Wyciągnij numer strony z formatu "6 # DAW_WYBOR_KONTROLI"
        link_target = None
        if link_target_raw:
            link_str = str(link_target_raw).split("#")[0].strip()
            try:
                link_target = str(int(link_str))
            except ValueError:
                link_target = link_str

        # Sortable — z layout lub enable-users-to.sort
        sortable = safe_get_bool(c, "layout.sortable")
        if not sortable:
            enable = c.get("enable-users-to", {})
            if isinstance(enable, dict) and "sort" in enable:
                sortable = bool(enable.get("sort"))

        column = Column(
            name=safe_get_str(ident, "column-name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            heading=safe_get_str(c, "heading.heading"),
            source_column=safe_get_str(source, "database-column"),
            data_type=safe_get_str(source, "data-type"),
            link_target=link_target,
            link_text=safe_get_str(link, "link-text"),
            link_clear_cache=safe_get_str(link, "target.clear-cache"),
            master_region=safe_get_str(c, "master-detail.master-region", strip_id=True),
            master_column=safe_get_str(c, "master-detail.master-column"),
            lov=safe_get_str(c, "list-of-values.list-of-values", strip_id=True),
            primary_key=safe_get_bool(source, "primary-key"),
            sortable=sortable,
            column_alignment=safe_get_str(c, "layout.column-alignment"),
            heading_alignment=safe_get_str(c, "heading.alignment"),
            escape_special_chars=safe_get_bool(c, "security.escape-special-characters") or None,
            compute_sum=safe_get_bool(c, "advanced.compute-sum") or None,
            sequence=safe_get_int(c, "layout.sequence") or None,
            build_option=safe_get_str(c, "configuration.build-option", strip_id=True),
        )
        columns.append(column)
    return columns


def _parse_items(items_data: list[dict]) -> list[PageItem]:
    """Parsuj elementy formularza strony."""
    items: list[PageItem] = []
    for item_data in items_data or []:
        ident = item_data.get("identification", {})
        source = item_data.get("source", {})
        layout = item_data.get("layout", {})
        session_state = item_data.get("session-state", {})
        security = item_data.get("security", {})
        settings = item_data.get("settings", {})

        # source_column tylko gdy typ źródła = Database Column
        source_type = safe_get_str(source, "type", "")
        source_column = None
        if source_type and "database" in source_type.lower():
            source_column = safe_get_str(source, "database-column")

        item = PageItem(
            name=safe_get_str(ident, "name", "") or "",
            type=safe_get_str(ident, "type", "") or "",
            label=safe_get_str(item_data, "label.label"),
            label_alignment=safe_get_str(item_data, "label.alignment"),
            source_column=source_column,
            lov=safe_get_str(item_data, "list-of-values.list-of-values", strip_id=True),
            lov_display_null_value=safe_get_str(item_data, "list-of-values.display-null-value"),
            lov_display_extra_values=safe_get_bool(item_data, "list-of-values.display-extra-values") or None,
            default_value=safe_get_str(item_data, "default.static-value"),
            data_type=safe_get_str(session_state, "data-type") if isinstance(session_state, dict) else None,
            storage=safe_get_str(session_state, "storage") if isinstance(session_state, dict) else None,
            session_state_protection=safe_get_str(security, "session-state-protection") if isinstance(security, dict) else None,
            store_encrypted=safe_get_bool(security, "store-value-encrypted-in-session-state") or None if isinstance(security, dict) else None,
            restricted_chars=safe_get_str(security, "restricted-characters") if isinstance(security, dict) else None,
            value_protected=safe_get_bool(settings, "value-protected") or None if isinstance(settings, dict) else None,
            region=safe_get_str(layout, "region", strip_id=True) if isinstance(layout, dict) else None,
            slot=safe_get_str(layout, "slot") if isinstance(layout, dict) else None,
            sequence=safe_get_int(layout, "sequence") or None if isinstance(layout, dict) else None,
            source_type=source_type or None,
            source_used=safe_get_str(source, "used"),
            source_primary_key=safe_get_bool(source, "primary-key") or None,
            source_query_only=safe_get_bool(source, "query-only") or None,
            form_region=safe_get_str(source, "form-region", strip_id=True),
            value_required=safe_get_bool(item_data, "validation.value-required") or None,
            validation_max_length=safe_get_int(item_data, "validation.maximum-length") or None,
            warn_on_unsaved=safe_get_str(item_data, "advanced.warn-on-unsaved-changes"),
            build_option=safe_get_str(item_data, "configuration.build-option", strip_id=True),
        )
        items.append(item)
    return items


def _parse_buttons(buttons_data: list[dict]) -> list[Button]:
    """Parsuj przyciski strony."""
    buttons: list[Button] = []
    for b in buttons_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})

        # Wyciągnij target page z behavior.target (jeśli redirect)
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
            confirmation_message=safe_get_str(b, "confirmation.message"),
            confirmation_style=safe_get_str(b, "confirmation.style"),
            server_side_condition=_compress_condition(b.get("server-side-condition")),
            build_option=safe_get_str(b, "configuration.build-option", strip_id=True),
        )
        buttons.append(button)
    return buttons


def _parse_processes(processes_data: list[dict]) -> list[Process]:
    """Parsuj procesy strony."""
    processes: list[Process] = []
    for p in processes_data or []:
        ident = p.get("identification", {})
        source = p.get("source", {})
        settings = p.get("settings", {})
        proc_type = safe_get_str(ident, "type", "") or ""

        # Kod — zależnie od typu procesu
        code = (
            safe_get(source, "pl/sql-code")
            or safe_get(source, "javascript-code")
        )

        # Procesy typu Invoke API — złóż opis z settings
        if not code and "invoke" in proc_type.lower():
            pkg = safe_get_str(settings, "package")
            proc = safe_get_str(settings, "procedure-or-function")
            if pkg or proc:
                code = f"INVOKE: {pkg or '?'}.{proc or '?'}"

        # Condition — cały blok server-side-condition jako string
        ssc = p.get("server-side-condition", {})
        condition = None
        btn_pressed = None
        if isinstance(ssc, dict):
            btn_pressed = safe_get_str(ssc, "when-button-pressed", strip_id=True)
            condition = _compress_condition(ssc)

        # Obsługa błędu
        error_block = p.get("error", {})
        error_display_location = None
        error_message = None
        if isinstance(error_block, dict):
            error_display_location = safe_get_str(error_block, "display-location")
            error_message = safe_get_str(error_block, "message")

        process = Process(
            name=safe_get_str(ident, "name", "") or "",
            type=proc_type,
            language=safe_get_str(source, "language"),
            point=safe_get_str(p, "execution.point", "") or "",
            code=code,
            condition=condition,
            when_button_pressed=btn_pressed,
            error_display_location=error_display_location,
            error_message=error_message,
            target_type=safe_get_str(settings, "target-type") if isinstance(settings, dict) else None,
            return_primary_key_after_insert=safe_get_bool(settings, "return-primary-key(s)-after-insert") or None if isinstance(settings, dict) else None,
            prevent_lost_updates=safe_get_bool(settings, "prevent-lost-updates") or None if isinstance(settings, dict) else None,
            lock_row=safe_get_bool(settings, "lock-row") or None if isinstance(settings, dict) else None,
            show_success_messages=safe_get_bool(settings, "show-success-messages") or None if isinstance(settings, dict) else None,
            success_message=safe_get_str(p, "success-message.success-message"),
            owner=safe_get_str(settings, "owner") if isinstance(settings, dict) else None,
            package=safe_get_str(settings, "package") if isinstance(settings, dict) else None,
            procedure_or_function=safe_get_str(settings, "procedure-or-function") if isinstance(settings, dict) else None,
            build_option=safe_get_str(p, "configuration.build-option", strip_id=True),
        )
        processes.append(process)
    return processes


def _parse_dynamic_actions(da_data: list[dict]) -> list[DynamicAction]:
    """Parsuj akcje dynamiczne z listą kroków."""
    dynamic_actions: list[DynamicAction] = []
    for da in da_data or []:
        ident = da.get("identification", {})
        when = da.get("when", {})

        # Trigger selector — próbuj kolejno: item, jquery-selector, region, button
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
            client_side_condition=safe_get_str(da, "client-side-condition.javascript-expression"),
            actions=_parse_da_steps(da.get("actions", [])),
            build_option=safe_get_str(da, "configuration.build-option", strip_id=True),
        )
        dynamic_actions.append(action)
    return dynamic_actions


def _parse_da_steps(steps_data: list[dict]) -> list[DynamicActionStep]:
    """Parsuj kroki akcji dynamicznej."""
    steps: list[DynamicActionStep] = []
    for s in steps_data or []:
        ident = s.get("identification", {})
        settings = s.get("settings", {})
        affected = s.get("affected-elements", {})

        # Kod z settings
        code = (
            safe_get(settings, "pl/sql-code")
            or safe_get(settings, "javascript-code")
        )

        # Affected elements — typ selekcji + selektor
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
            maintain_pagination=safe_get_bool(settings, "maintain-pagination") or None if isinstance(settings, dict) else None,
            show_processing=safe_get_bool(settings, "show-processing") or None if isinstance(settings, dict) else None,
            items_to_submit=safe_get_str(settings, "items-to-submit") if isinstance(settings, dict) else None,
        )
        steps.append(step)
    return steps


def _parse_branches(branches_data: list[dict]) -> list[Branch]:
    """Parsuj rozgałęzienia nawigacyjne."""
    branches: list[Branch] = []
    for b in branches_data or []:
        ident = b.get("identification", {})
        behavior = b.get("behavior", {})
        target = behavior.get("target", {}) if isinstance(behavior, dict) else {}

        # Numer strony docelowej
        target_page = None
        page_raw = safe_get(target, "page") if isinstance(target, dict) else None
        if page_raw:
            try:
                target_page = int(str(page_raw).split("#")[0].strip())
            except ValueError:
                pass

        # Condition — filtruj kluczowe pola (analogicznie do procesów)
        ssc = b.get("server-side-condition", {})
        condition = _compress_condition(ssc)

        branch = Branch(
            name=safe_get_str(ident, "name"),
            type=safe_get_str(behavior, "type", "") or "" if isinstance(behavior, dict) else "",
            target_page=target_page,
            target_url=safe_get(target, "url") if isinstance(target, dict) else None,
            point=safe_get_str(b, "execution.point", "") or "",
            condition=condition,
            build_option=safe_get_str(b, "configuration.build-option", strip_id=True),
        )
        branches.append(branch)
    return branches


def _parse_validations(validations_data: list[dict]) -> list[Validation]:
    """Parsuj walidacje strony."""
    validations: list[Validation] = []
    for v in validations_data or []:
        ident = v.get("identification", {})
        val_block = v.get("validation", {})

        # Condition
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
            build_option=safe_get_str(v, "configuration.build-option", strip_id=True),
        )
        validations.append(validation)
    return validations


def _parse_computations(computations_data: list[dict] | None) -> list[Computation]:
    """Parsuj komputacje strony (wartości itemów liczone serwerowo)."""
    computations: list[Computation] = []
    for c in computations_data or []:
        ident = c.get("identification", {})
        computation = c.get("computation", {})

        # Kod — może być w polach pl/sql-expression, pl/sql-code lub sql-expression
        code = (
            safe_get(computation, "pl/sql-expression")
            or safe_get(computation, "pl/sql-code")
            or safe_get(computation, "sql-expression")
            or safe_get(computation, "expression")
        )

        comp = Computation(
            item_name=safe_get_str(ident, "item-name", "") or "",
            point=safe_get_str(c, "execution.point", "") or "",
            type=safe_get_str(computation, "type", "") or "",
            language=safe_get_str(computation, "language"),
            code=code,
            build_option=safe_get_str(c, "configuration.build-option", strip_id=True),
        )
        computations.append(comp)
    return computations
