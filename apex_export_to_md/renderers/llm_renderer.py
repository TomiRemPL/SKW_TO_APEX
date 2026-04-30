"""LLM Renderer — generuje skondensowany format liniowy zoptymalizowany pod tokenizer.

Minimalizuje zużycie tokenów przy zachowaniu pełnej informacji.
Format: prefiksy typu (APP, PAGE, RGN, COL, ITEM, BTN, PROC, DA, ...) z wartościami
oddzielonymi znakiem |.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)


class LLMRenderer(BaseRenderer):
    """Renderer zoptymalizowany dla LLM — format liniowy."""

    def render(self, app: ApexApp) -> str:
        """Generuj skondensowany tekst."""
        lines: list[str] = []

        # Nagłówek aplikacji
        lines.append(f"APP:{app.id}|{app.alias}|{app.name}")

        # Strony
        for page in app.pages:
            lines.extend(self._render_page(page))

        # Shared components
        if self._config.include_shared_components:
            lines.extend(self._render_shared(app))

        return "\n".join(lines)

    def _render_page(self, page: ApexPage) -> list[str]:
        """Renderuj stronę w formacie liniowym."""
        lines: list[str] = []

        auth = "auth:required" if page.security.get("authentication") else ""
        parts = [f"===PAGE:{page.id}", page.name, page.page_mode]
        if auth:
            parts.append(auth)
        lines.append("|".join(parts))

        if page.raw_attributes:
            attr_str = self._flatten_to_string(page.raw_attributes)
            if attr_str:
                lines.append(f"PAGE_ATTRS:{attr_str}")

        if page.css_inline:
            lines.append("CSS:inline")
            lines.append(page.css_inline)
            lines.append("---")
        if page.js_inline:
            lines.append("JS:inline")
            lines.append(page.js_inline)
            lines.append("---")

        for region in page.regions:
            lines.extend(self._render_region(region))

        for item in page.items:
            parts = [f"ITEM:{item.name}", item.type]
            if item.label:
                parts.append(f"label:{item.label}")
            if item.source_column:
                parts.append(f"col:{item.source_column}")
            if item.lov:
                parts.append(f"lov:{item.lov}")
            lines.append("|".join(parts))
            if item.raw_attributes:
                attr_str = self._flatten_to_string(item.raw_attributes)
                if attr_str:
                    lines.append(f"ITEM_ATTRS:{attr_str}")

        for btn in page.buttons:
            parts = [f"BTN:{btn.name}"]
            if btn.label:
                parts.append(f"label:{btn.label}")
            if btn.action:
                parts.append(f"action:{btn.action}")
            if btn.is_hot:
                parts.append("hot:true")
            if btn.target_page:
                parts.append(f"target:page{btn.target_page}")
            lines.append("|".join(parts))
            if btn.raw_attributes:
                attr_str = self._flatten_to_string(btn.raw_attributes)
                if attr_str:
                    lines.append(f"BTN_ATTRS:{attr_str}")

        for proc in page.processes:
            parts = [f"PROC:{proc.name}", proc.type]
            if proc.language:
                parts.append(f"lang:{proc.language}")
            parts.append(f"point:{proc.point}")
            if proc.when_button_pressed:
                parts.append(f"btn:{proc.when_button_pressed}")
            lines.append("|".join(parts))
            if proc.code:
                lang = (proc.language or "sql").lower().replace("/", "")
                lines.extend(self._render_code_or_summary(proc.code, lang))
            if proc.raw_attributes:
                attr_str = self._flatten_to_string(proc.raw_attributes)
                if attr_str:
                    lines.append(f"PROC_ATTRS:{attr_str}")

        for da in page.dynamic_actions:
            parts = [f"DA:{da.name}", f"event:{da.event}"]
            if da.selection_type:
                parts.append(f"sel:{da.selection_type}")
            if da.trigger_selector:
                parts.append(f"trigger:{da.trigger_selector}")
            if da.event_scope:
                parts.append(f"scope:{da.event_scope}")
            lines.append("|".join(parts))
            for step in da.actions:
                step_parts = [f"DA_STEP:{step.type}"]
                if step.affected_elements:
                    step_parts.append(f"affects:{step.affected_elements}")
                lines.append("|".join(step_parts))
                if step.code:
                    lines.extend(self._render_code_or_summary(step.code, "plsql"))
                if step.raw_attributes:
                    attr_str = self._flatten_to_string(step.raw_attributes)
                    if attr_str:
                        lines.append(f"DA_STEP_ATTRS:{attr_str}")
            if da.raw_attributes:
                attr_str = self._flatten_to_string(da.raw_attributes)
                if attr_str:
                    lines.append(f"DA_ATTRS:{attr_str}")

        for branch in page.branches:
            target = f"page:{branch.target_page}" if branch.target_page else branch.target_url or "?"
            parts = [f"BRANCH:{branch.type}->{target}"]
            if branch.condition:
                parts.append(f"cond:{branch.condition}")
            lines.append("|".join(parts))
            if branch.raw_attributes:
                attr_str = self._flatten_to_string(branch.raw_attributes)
                if attr_str:
                    lines.append(f"BRANCH_ATTRS:{attr_str}")

        for val in page.validations:
            parts = [f"VAL:{val.name}", f"type:{val.type}"]
            lines.append("|".join(parts))
            if val.code:
                lines.extend(self._render_code_or_summary(val.code, "plsql"))
            if val.raw_attributes:
                attr_str = self._flatten_to_string(val.raw_attributes)
                if attr_str:
                    lines.append(f"VAL_ATTRS:{attr_str}")

        return lines

    def _render_region(self, region: Region) -> list[str]:
        """Renderuj region i jego kolumny."""
        lines: list[str] = []
        parts = [f"RGN:{region.name}"]
        if region.title:
            parts.append(f"title:{region.title}")
        parts.append(region.type)
        if region.source_table:
            parts.append(f"src:{region.source_table}")
        if region.source_sql and self._should_include_code():
            parts.append("src:SQL")
        if region.editable:
            parts.append("edit:true")
            if region.allowed_operations:
                ops = ",".join(o.split(" ")[0] for o in region.allowed_operations)
                parts.append(f"ops:{ops}")
        if region.parent_region:
            parts.append(f"parent:{region.parent_region}")
        lines.append("|".join(parts))

        if region.source_sql and self._should_include_code():
            lines.append("```sql")
            lines.append(region.source_sql)
            lines.append("```")

        if region.raw_attributes:
            attr_str = self._flatten_to_string(region.raw_attributes)
            if attr_str:
                lines.append(f"RGN_ATTRS:{attr_str}")

        for col in region.columns:
            col_parts = [f"COL:{col.name}", col.type]
            if col.heading:
                col_parts.append(f"heading:{col.heading}")
            if col.primary_key:
                col_parts.append("pk:true")
            if col.link_target:
                col_parts.append(f"link:page{col.link_target}")
            if col.lov:
                col_parts.append(f"lov:{col.lov}")
            lines.append("|".join(col_parts))
            if col.raw_attributes:
                attr_str = self._flatten_to_string(col.raw_attributes)
                if attr_str:
                    lines.append(f"COL_ATTRS:{attr_str}")

        return lines

    def _flatten_to_string(self, d: dict, prefix: str = "") -> str:
        """Spłaszcz słownik do formatu 'k1=v1;k2.nested=v2'."""
        parts = []
        for key, value in d.items():
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                nested = self._flatten_to_string(value, full_key + ".")
                if nested:
                    parts.append(nested)
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    parts.append(f"{full_key}={','.join(str(v) for v in value)}")
            elif value is not None and value is not False and value != "":
                parts.append(f"{full_key}={value}")
        return ";".join(parts)

    def _render_shared(self, app: ApexApp) -> list[str]:
        """Renderuj shared components."""
        lines: list[str] = []

        for lov in app.lovs:
            parts = [f"===LOV:{lov.name}"]
            # Skrócony typ
            type_short = {"Table / View": "Table", "SQL Query": "SQL",
                          "Static Values": "Static"}.get(lov.source_type, lov.source_type)
            parts.append(f"type:{type_short}")
            if lov.source_table:
                parts.append(f"tbl:{lov.source_table}")
            if lov.return_column:
                parts.append(f"ret:{lov.return_column}")
            if lov.display_column:
                parts.append(f"disp:{lov.display_column}")
            lines.append("|".join(parts))
            if lov.sql_query and self._should_include_code():
                lines.append("```sql")
                lines.append(lov.sql_query)
                lines.append("```")
            if lov.entries:
                vals = "|".join(f"{e['display']}:{e['return']}" for e in lov.entries)
                lines.append(f"ENTRIES:{vals}")

        for auth in app.authorizations:
            parts = [f"===AUTH:{auth.name}"]
            if auth.type:
                parts.append(f"type:{auth.type}")
            if auth.role_or_group:
                parts.append(f"role:{auth.role_or_group}")
            lines.append("|".join(parts))
            if auth.code and self._should_include_code():
                lines.append("```plsql")
                lines.append(auth.code)
                lines.append("```")

        for nav in app.nav_lists:
            entries_str = "|".join(
                f"{e.get('label', '?')}->page:{e.get('target_page', '?')}"
                for e in nav.entries
            )
            lines.append(f"===NAV:{nav.name}|{entries_str}")

        for item in app.app_items:
            lines.append(f"===APP_ITEM:{item.name}|scope:{item.scope or '?'}")

        for bo in app.build_options:
            lines.append(f"===BUILD_OPT:{bo.name}|status:{bo.status}")

        for bc in app.breadcrumbs:
            entries_str = "->".join(
                f"{e.get('name', '?')}:page{e.get('page_number', '?')}"
                for e in bc.entries
            )
            lines.append(f"===BREADCRUMB:{bc.name}|{entries_str}")

        for role in app.acl_roles:
            lines.append(f"===ACL:{role.name}|static_id:{role.static_id or '?'}")

        return lines
