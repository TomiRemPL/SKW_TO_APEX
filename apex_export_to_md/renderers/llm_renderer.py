"""LLM Renderer — generuje skondensowany format liniowy zoptymalizowany pod tokenizer.

Minimalizuje zużycie tokenów przy zachowaniu pełnej informacji.
Format: prefiksy typu (APP, PAGE, RGN, COL, ITEM, BTN, PROC, DA, ...) z wartościami
oddzielonymi znakiem |.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, Computation, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
    Authentication, Plugin, SearchConfig, DataLoadDef, StaticFile, PageGroup,
)


class LLMRenderer(BaseRenderer):
    """Renderer zoptymalizowany dla LLM — format liniowy."""

    def render(self, app: ApexApp) -> str:
        """Generuj skondensowany tekst."""
        lines: list[str] = []

        # Nagłówek aplikacji
        lines.append(f"APP:{app.id}|{app.alias}|{app.name}")

        # Metadane (z pliku f*.sql)
        if app.metadata:
            meta = app.metadata
            parts = []
            if meta.apex_version:
                parts.append(f"APEX={meta.apex_version}")
            if meta.owner:
                parts.append(f"OWNER={meta.owner}")
            if meta.version:
                parts.append(f"VER={meta.version}")
            if meta.language:
                parts.append(f"LANG={meta.language}")
            if meta.is_pwa:
                parts.append("PWA=Y")
            if meta.compatibility_mode:
                parts.append(f"COMPAT={meta.compatibility_mode}")
            if meta.page_protection_enabled:
                parts.append("PAGE_PROTECTION=Y")
            if meta.bookmark_checksum_function:
                parts.append(f"BOOKMARK_CHECKSUM={meta.bookmark_checksum_function}")
            if meta.exact_substitutions_only:
                parts.append("EXACT_SUBS=Y")
            if meta.runtime_api_usage:
                parts.append(f"RUNTIME_API={meta.runtime_api_usage}")
            if meta.security_scheme:
                parts.append(f"SECURITY={meta.security_scheme}")
            if meta.rejoin_existing_sessions:
                parts.append(f"SESSION_REJOIN={meta.rejoin_existing_sessions}")
            if meta.page_view_logging:
                parts.append("VIEW_LOGGING=Y")
            if meta.flow_status:
                parts.append(f"STATUS={meta.flow_status}")
            if meta.file_storage:
                parts.append(f"FILE_STORAGE={meta.file_storage}")
            if meta.files_version:
                parts.append(f"FILES_VER={meta.files_version}")
            if meta.working_copy_name:
                parts.append(f"WORKING_COPY={meta.working_copy_name}")
            if meta.pages_count:
                parts.append(f"PAGES={meta.pages_count}")
            if meta.regions_count:
                parts.append(f"REGIONS={meta.regions_count}")
            if parts:
                lines.append(f"META:|{'|'.join(parts)}")
            if meta.substitutions:
                subs = "|".join(f"{k}={v}" for k, v in meta.substitutions.items())
                lines.append(f"SUBS:|{subs}")

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

        # Nagłówek strony
        auth = "auth:required" if page.security.get("authentication") else ""
        parts = [f"===PAGE:{page.id}", page.name, page.page_mode]
        if page.page_template:
            parts.append(f"tpl:{page.page_template}")
        if page.page_group:
            parts.append(f"grp:{page.page_group}")
        if auth:
            parts.append(auth)
        if page.help_text:
            parts.append(f"help:{page.help_text}")
        if page.dialog:
            dialog_str = ",".join(f"{k}={v}" for k, v in page.dialog.items())
            parts.append(f"dialog:{dialog_str}")
        lines.append("|".join(parts))

        # CSS/JS
        if page.css_inline:
            lines.append("CSS:inline")
            lines.append(page.css_inline)
            lines.append("---")
        if page.javascript_full:
            lines.append("JS:func_and_global")
            lines.append(page.javascript_full)
            lines.append("---")
        if page.js_inline:
            lines.append("JS:inline")
            lines.append(page.js_inline)
            lines.append("---")

        # Komputacje strony
        for comp in page.computations:
            comp_parts = [f"COMPUTATION:{comp.item_name}"]
            if comp.point:
                comp_parts.append(f"point:{comp.point}")
            if comp.type:
                comp_parts.append(f"type:{comp.type}")
            if comp.language:
                comp_parts.append(f"lang:{comp.language}")
            if comp.build_option:
                comp_parts.append(f"build_opt:{comp.build_option}")
            lines.append("|".join(comp_parts))
            if comp.code:
                lines.extend(self._render_code_or_summary(comp.code, "plsql"))

        # Regiony
        for region in page.regions:
            lines.extend(self._render_region(region))

        # Elementy formularza
        for item in page.items:
            parts = [f"ITEM:{item.name}", item.type]
            if item.label:
                parts.append(f"label:{item.label}")
            if item.source_column:
                parts.append(f"col:{item.source_column}")
            if item.data_type:
                parts.append(f"dtype:{item.data_type}")
            if item.storage:
                parts.append(f"storage:{item.storage}")
            if item.session_state_protection:
                parts.append(f"protection:{item.session_state_protection}")
            if item.store_encrypted:
                parts.append("encrypted:true")
            if item.region:
                parts.append(f"region:{item.region}")
            if item.slot:
                parts.append(f"slot:{item.slot}")
            if item.sequence is not None:
                parts.append(f"seq:{item.sequence}")
            if item.source_type:
                parts.append(f"src_type:{item.source_type}")
            if item.form_region:
                parts.append(f"form_region:{item.form_region}")
            if item.source_primary_key:
                parts.append("src_pk:true")
            if item.source_query_only:
                parts.append("query_only:true")
            if item.value_required:
                parts.append("required:true")
            if item.validation_max_length:
                parts.append(f"max_len:{item.validation_max_length}")
            if item.lov:
                parts.append(f"lov:{item.lov}")
            if item.lov_display_null_value:
                parts.append(f"lov_null:{item.lov_display_null_value}")
            if item.lov_display_extra_values:
                parts.append("lov_extra:true")
            if item.default_value:
                parts.append(f"default:{item.default_value}")
            if item.build_option:
                parts.append(f"build_opt:{item.build_option}")
            lines.append("|".join(parts))

        # Przyciski
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
            if btn.confirmation_message:
                parts.append(f"confirm:{btn.confirmation_message}")
            if btn.server_side_condition:
                parts.append(f"ssc:{btn.server_side_condition}")
            if btn.build_option:
                parts.append(f"build_opt:{btn.build_option}")
            lines.append("|".join(parts))

        # Procesy
        for proc in page.processes:
            parts = [f"PROC:{proc.name}", proc.type]
            if proc.language:
                parts.append(f"lang:{proc.language}")
            parts.append(f"point:{proc.point}")
            if proc.when_button_pressed:
                parts.append(f"btn:{proc.when_button_pressed}")
            if proc.condition:
                parts.append(f"cond:{proc.condition}")
            if proc.error_display_location:
                parts.append(f"err_loc:{proc.error_display_location}")
            if proc.error_message:
                parts.append(f"err_msg:{proc.error_message}")
            if proc.target_type:
                parts.append(f"target:{proc.target_type}")
            if proc.return_primary_key_after_insert:
                parts.append("return_pk:true")
            if proc.prevent_lost_updates:
                parts.append("prevent_lost_update:true")
            if proc.lock_row:
                parts.append("lock_row:true")
            if proc.success_message:
                parts.append(f"success:{proc.success_message}")
            if proc.package or proc.procedure_or_function:
                parts.append(f"proc:{proc.owner + '.' if proc.owner else ''}{proc.package or '?'}.{proc.procedure_or_function or '?'}")
            if proc.build_option:
                parts.append(f"build_opt:{proc.build_option}")
            lines.append("|".join(parts))
            if proc.code:
                lang = (proc.language or "sql").lower().replace("/", "")
                lines.extend(self._render_code_or_summary(proc.code, lang))

        # Akcje dynamiczne
        for da in page.dynamic_actions:
            parts = [f"DA:{da.name}", f"event:{da.event}"]
            if da.selection_type:
                parts.append(f"sel:{da.selection_type}")
            if da.trigger_selector:
                parts.append(f"trigger:{da.trigger_selector}")
            if da.event_scope:
                parts.append(f"scope:{da.event_scope}")
            if da.client_side_condition:
                parts.append(f"client_cond:{da.client_side_condition}")
            if da.build_option:
                parts.append(f"build_opt:{da.build_option}")
            lines.append("|".join(parts))
            for step in da.actions:
                step_parts = [f"DA_STEP:{step.type}"]
                if step.affected_elements:
                    step_parts.append(f"affects:{step.affected_elements}")
                if step.fire_on_initialization:
                    step_parts.append("init:true")
                if step.maintain_pagination:
                    step_parts.append("keep_page:true")
                if step.items_to_submit:
                    step_parts.append(f"submit:{step.items_to_submit}")
                lines.append("|".join(step_parts))
                if step.code:
                    lines.extend(self._render_code_or_summary(step.code, "plsql"))

        # Rozgałęzienia
        for branch in page.branches:
            target = f"page:{branch.target_page}" if branch.target_page else branch.target_url or "?"
            parts = [f"BRANCH:{branch.type}->{target}"]
            if branch.point:
                parts.append(f"point:{branch.point}")
            if branch.condition:
                parts.append(f"cond:{branch.condition}")
            if branch.build_option:
                parts.append(f"build_opt:{branch.build_option}")
            lines.append("|".join(parts))

        # Walidacje
        for val in page.validations:
            parts = [f"VAL:{val.name}", f"type:{val.type}"]
            if val.condition:
                parts.append(f"cond:{val.condition}")
            if val.build_option:
                parts.append(f"build_opt:{val.build_option}")
            lines.append("|".join(parts))
            if val.code:
                lines.extend(self._render_code_or_summary(val.code, "plsql"))

        return lines

    def _render_region(self, region: Region) -> list[str]:
        """Renderuj region i jego kolumny."""
        lines: list[str] = []
        parts = [f"RGN:{region.name}"]
        if region.title:
            parts.append(f"title:{region.title}")
        parts.append(region.type)
        if region.template:
            parts.append(f"tpl:{region.template}")
        if region.template_options:
            parts.append(f"tpl_opts:{','.join(region.template_options)}")
        if region.slot:
            parts.append(f"slot:{region.slot}")
        if region.sequence is not None:
            parts.append(f"seq:{region.sequence}")
        if region.source_location:
            parts.append(f"src_loc:{region.source_location}")
        if region.source_table:
            source = f"{region.source_owner}." if region.source_owner else ""
            parts.append(f"src:{source}{region.source_table}")
        if region.source_where:
            parts.append(f"where:{region.source_where}")
        if region.page_items_to_submit:
            parts.append(f"submit:{region.page_items_to_submit}")
        if region.lost_update_type:
            parts.append(f"lost_update:{region.lost_update_type}")
        if region.source_sql and self._should_include_code():
            parts.append("src:SQL")
        if region.editable:
            parts.append("edit:true")
            if region.allowed_operations:
                ops = ",".join(o.split(" ")[0] for o in region.allowed_operations)
                parts.append(f"ops:{ops}")
        if region.server_side_condition:
            parts.append(f"ssc:{region.server_side_condition}")
        if region.server_cache:
            parts.append(f"cache:{region.server_cache}")
        if region.pagination:
            parts.append(f"pagination:{region.pagination}")
        if region.order_by:
            parts.append(f"order:{region.order_by}")
        if region.build_option:
            parts.append(f"build_opt:{region.build_option}")
        lines.append("|".join(parts))

        # SQL źródłowy
        if region.source_sql and self._should_include_code():
            lines.append("```sql")
            lines.append(region.source_sql)
            lines.append("```")

        # Kolumny
        for col in region.columns:
            col_parts = [f"COL:{col.name}", col.type]
            if col.heading:
                col_parts.append(f"heading:{col.heading}")
            if col.primary_key:
                col_parts.append("pk:true")
            if col.sortable:
                col_parts.append("sort:true")
            if col.column_alignment:
                col_parts.append(f"align:{col.column_alignment}")
            if col.heading_alignment:
                col_parts.append(f"head_align:{col.heading_alignment}")
            if col.escape_special_chars is not None:
                col_parts.append(f"escape:{col.escape_special_chars}")
            if col.compute_sum:
                col_parts.append("sum:true")
            if col.sequence is not None:
                col_parts.append(f"seq:{col.sequence}")
            if col.link_target:
                col_parts.append(f"link:page{col.link_target}")
            if col.link_text:
                col_parts.append(f"link_text:{col.link_text}")
            if col.master_region or col.master_column:
                col_parts.append(f"master:{col.master_region or '?'}.{col.master_column or '?'}")
            if col.lov:
                col_parts.append(f"lov:{col.lov}")
            if col.build_option:
                col_parts.append(f"build_opt:{col.build_option}")
            lines.append("|".join(col_parts))

        return lines

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

        for auth_s in app.authentications:
            parts = [f"===AUTH_SCHEME:{auth_s.name}"]
            if auth_s.type:
                parts.append(f"type:{auth_s.type}")
            if auth_s.host:
                parts.append(f"host:{auth_s.host}")
            if auth_s.port:
                parts.append(f"port:{auth_s.port}")
            if auth_s.use_ssl:
                parts.append(f"ssl:{auth_s.use_ssl}")
            if auth_s.dn_string:
                parts.append(f"dn:{auth_s.dn_string}")
            lines.append("|".join(parts))

        for p in app.plugins:
            parts = [f"===PLUGIN:{p.name}"]
            if p.internal_name:
                parts.append(f"int:{p.internal_name}")
            if p.theme:
                parts.append(f"theme:{p.theme}")
            if p.plugin_type:
                parts.append(f"type:{p.plugin_type}")
            lines.append("|".join(parts))

        for s in app.search_configs:
            parts = [f"===SEARCH_CFG:{s.name}"]
            if s.search_type:
                parts.append(f"type:{s.search_type}")
            if s.location:
                parts.append(f"loc:{s.location}")
            lines.append("|".join(parts))
            if s.sql_query and self._should_include_code():
                lines.append("```sql")
                lines.append(s.sql_query)
                lines.append("```")

        for d in app.data_load_defs:
            parts = [f"===DATA_LOAD:{d.name}"]
            if d.table_name:
                parts.append(f"tbl:{d.table_name}")
            if d.loading_method:
                parts.append(f"method:{d.loading_method}")
            if d.commit_interval:
                parts.append(f"commit:{d.commit_interval}")
            lines.append("|".join(parts))

        for f in app.static_files:
            parts = [f"===STATIC_FILE:{f.file_name}"]
            if f.mime_type:
                parts.append(f"mime:{f.mime_type}")
            lines.append("|".join(parts))

        for g in app.page_groups:
            lines.append(f"===PAGE_GROUP:{g.name}")

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

