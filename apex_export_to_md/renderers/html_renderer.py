"""HTML Renderer — generuje interaktywną dokumentację HTML.

Odwzorowuje format referencyjny apex_export_interactive.html:
- 3 zakładki: Diagram relacji, Baza danych, APEX ↔ DB
- vis-network.js do interaktywnego diagramu ER
- Prism.js do podświetlania składni
- Kolorystyka: #1a365d (navy), #d4a843 (gold)
"""
from __future__ import annotations
import html as html_mod
import json
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp


class HTMLRenderer(BaseRenderer):
    """Renderer generujący interaktywną dokumentację HTML."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny dokument HTML."""
        data_json = self._build_data_json(app)
        title = f"{app.name} \u2014 Dokumentacja projektu"
        title_esc = html_mod.escape(title)

        return (
            self._html_head(title_esc)
            + self._html_body(title_esc, app)
            + "\n<script>\nconst DATA = "
            + data_json
            + ";\n</script>\n"
            + self._html_scripts()
            + "\n<script>\n"
            + self._app_js()
            + "\n</script>\n</body>\n</html>"
        )

    # ------------------------------------------------------------------
    # HTML skeleton
    # ------------------------------------------------------------------
    def _html_head(self, title: str) -> str:
        generation_meta = f'<meta name="generation-date" content="{self._timestamp}">' if self._timestamp else ''
        return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{generation_meta}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
{self._css()}
</head>
"""

    def _html_body(self, title: str, app: ApexApp) -> str:
        info_tab_content = self._render_info_tab(app)
        return f"""<body>

<header>
  <div class="header-left">
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="19" fill="#1a365d" stroke="#d4a843" stroke-width="2"/>
      <text x="20" y="26" text-anchor="middle" font-family="Arial,sans-serif"
            font-size="16" font-weight="bold" fill="#d4a843">TR</text>
    </svg>
    <h1>{title}</h1>
  </div>
  <div class="search-box">
    <input type="text" id="search" placeholder="Szukaj..." oninput="handleSearch(this.value)">
  </div>
</header>

<nav class="tabs">
  <button class="tab active" onclick="switchTab('info')">Informacje</button>
  <button class="tab" onclick="switchTab('diagram')">Diagram relacji</button>
  <button class="tab" onclick="switchTab('browser')">Baza danych</button>
  <button class="tab" onclick="switchTab('map')">APEX \u2194 DB</button>
</nav>

<main>
  <div id="tab-info" class="tab-content active">
{info_tab_content}
  </div>

  <div id="tab-diagram" class="tab-content" style="display:none">
    <div id="er-network" style="width:100%;height:600px;border:1px solid #ddd;"></div>
    <div id="node-detail" class="detail-panel"></div>
  </div>

  <div id="tab-browser" class="tab-content" style="display:none">
    <div class="browser-layout">
      <div id="object-tree" class="tree-panel"></div>
      <div id="object-detail" class="detail-panel"></div>
    </div>
  </div>

  <div id="tab-map" class="tab-content" style="display:none">
    <div class="map-layout">
      <div class="map-sidebar">
        <div id="apex-pages" class="map-column">
          <h3>Strony APEX</h3>
          <div id="page-list"></div>
        </div>
        <div id="db-objects" class="map-column">
          <h3>Obiekty bazy danych</h3>
          <div id="db-list"></div>
        </div>
      </div>
      <div id="page-detail-panel" class="page-detail-panel">
        <div class="page-detail-placeholder">
          \u2190 Kliknij na stron\u0119 APEX, aby zobaczy\u0107 szczeg\u00f3\u0142y
        </div>
      </div>
    </div>
  </div>
</main>

<footer>
  <span>Wygenerowano narz\u0119dziem <strong>apex_export_to_md</strong></span>
  <span>Autor: <strong>Tomasz Rembiasz</strong></span>
</footer>
"""

    def _render_info_tab(self, app: ApexApp) -> str:
        """Generuj zawartość zakładki Informacje o projekcie."""
        meta = app.metadata
        lines: list[str] = []
        lines.append('    <div class="info-container">')

        # Sekcja nagłówkowa
        lines.append('      <div class="info-header">')
        lines.append(f'        <h2>{html_mod.escape(app.name)}</h2>')
        if meta and meta.copyright:
            lines.append(f'        <p class="info-subtitle">{html_mod.escape(meta.copyright)}</p>')
        lines.append('      </div>')

        # Parametry aplikacji
        lines.append('      <div class="info-grid">')
        lines.append('        <div class="info-card">')
        lines.append('          <h3>Parametry aplikacji</h3>')
        lines.append('          <table class="info-table">')
        lines.append(f'            <tr><td>ID aplikacji</td><td><strong>{html_mod.escape(app.id)}</strong></td></tr>')
        lines.append(f'            <tr><td>Alias</td><td><strong>{html_mod.escape(app.alias)}</strong></td></tr>')
        if meta:
            if meta.version:
                lines.append(f'            <tr><td>Wersja</td><td>{html_mod.escape(meta.version)}</td></tr>')
            if meta.apex_version:
                lines.append(f'            <tr><td>Wersja APEX</td><td>{html_mod.escape(meta.apex_version)}</td></tr>')
            if meta.owner:
                lines.append(f'            <tr><td>Schemat (owner)</td><td>{html_mod.escape(meta.owner)}</td></tr>')
            if meta.language:
                lang_name = {"pl": "polski", "en": "angielski"}.get(meta.language, meta.language)
                lines.append(f'            <tr><td>Język</td><td>{html_mod.escape(lang_name)}</td></tr>')
            if meta.exported_by:
                lines.append(f'            <tr><td>Eksportowane przez</td><td>{html_mod.escape(meta.exported_by)}</td></tr>')
        lines.append('          </table>')
        lines.append('        </div>')

        # Funkcjonalności
        if meta:
            lines.append('        <div class="info-card">')
            lines.append('          <h3>Funkcjonalności</h3>')
            lines.append('          <table class="info-table">')
            if meta.is_pwa:
                lines.append('            <tr><td>PWA</td><td><span class="badge badge-yes">Tak</span></td></tr>')
            if meta.pwa_installable:
                lines.append('            <tr><td>Instalowalna</td><td><span class="badge badge-yes">Tak</span></td></tr>')
            if meta.push_enabled:
                lines.append('            <tr><td>Push Notifications</td><td><span class="badge badge-yes">Tak</span></td></tr>')
            cache_text = "Wyłączone" if not meta.browser_cache else "Włączone"
            lines.append(f'            <tr><td>Cache przeglądarki</td><td>{cache_text}</td></tr>')
            lines.append('          </table>')
            lines.append('        </div>')

            technical_settings = [
              ("Tryb zgodności APEX", meta.compatibility_mode),
              ("Ochrona stron", "Włączona" if meta.page_protection_enabled else ""),
              ("Algorytm checksum bookmarków", meta.bookmark_checksum_function),
              ("Wymuszanie dokładnych zmiennych substytucyjnych",
               "Tak" if meta.exact_substitutions_only else ""),
              ("Dostęp Runtime API", meta.runtime_api_usage),
              ("Schemat bezpieczeństwa", meta.security_scheme),
              ("Ponowne dołączanie do sesji", meta.rejoin_existing_sessions),
              ("Logowanie odsłon", "Włączone" if meta.page_view_logging else ""),
              ("Status aplikacji", meta.flow_status),
              ("Magazyn plików statycznych", meta.file_storage),
              ("Wersja plików statycznych", str(meta.files_version) if meta.files_version else ""),
              ("Kopia robocza", meta.working_copy_name),
              ("Autor kopii roboczej", meta.working_copy_created_by),
            ]
            technical_settings = [(label, value) for label, value in technical_settings if value]
            if technical_settings:
              lines.append('        <div class="info-card">')
              lines.append('          <h3>Konfiguracja techniczna</h3>')
              lines.append('          <table class="info-table">')
              for label, value in technical_settings:
                lines.append(
                  f'            <tr><td>{html_mod.escape(label)}</td>'
                  f'<td>{html_mod.escape(value)}</td></tr>'
                )
              lines.append('          </table>')
              lines.append('        </div>')

        # Statystyki
        if meta and meta.pages_count:
            lines.append('        <div class="info-card">')
            lines.append('          <h3>Statystyki eksportu</h3>')
            lines.append('          <div class="stats-grid">')
            stats = [
                ("Strony", meta.pages_count),
                ("Regiony", meta.regions_count),
                ("Elementy", meta.items_count),
                ("Przyciski", meta.buttons_count),
                ("Procesy", meta.processes_count),
                ("Akcje dyn.", meta.dynamic_actions_count),
                ("Walidacje", meta.validations_count),
                ("LOV", meta.lovs_count),
                ("Listy", meta.lists_count),
                ("Build Opt.", meta.build_options_count),
            ]
            for label, count in stats:
                if count:
                    lines.append(f'            <div class="stat-item"><span class="stat-value">{count}</span><span class="stat-label">{label}</span></div>')
            lines.append('          </div>')
            lines.append('        </div>')

        # Zmienne substytucyjne
        if meta and meta.substitutions:
            lines.append('        <div class="info-card">')
            lines.append('          <h3>Zmienne substytucyjne</h3>')
            lines.append('          <table class="info-table">')
            for key, val in meta.substitutions.items():
                lines.append(f'            <tr><td><code>{html_mod.escape(key)}</code></td><td>{html_mod.escape(val)}</td></tr>')
            lines.append('          </table>')
            lines.append('        </div>')

        lines.append('      </div>')  # info-grid
        lines.append('    </div>')  # info-container
        return "\n".join(lines)

    def _html_scripts(self) -> str:
        return """<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sql.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-plsql.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js"></script>"""

    # ------------------------------------------------------------------
    # DATA JSON builder
    # ------------------------------------------------------------------
    def _build_data_json(self, app: ApexApp) -> str:
        data: dict = {
            "tables": [],
            "views": [],
            "packages": [],
            "sequences": [],
            "triggers": [],
            "edges": [],
            "pages": [],
            "links": [],
        }

        ddl = app.ddl_schema

        if ddl:
            for t in ddl.tables:
                table_obj: dict = {
                    "name": t.name,
                    "comment": t.comment or "",
                    "columns": [],
                    "constraints": [],
                    "indexes": [],
                }
                for col in t.columns:
                    col_comment = t.column_comments.get(col.name, "")
                    table_obj["columns"].append({
                        "name": col.name,
                        "type": col.data_type,
                        "nullable": col.nullable,
                        "default": col.default or "",
                        "identity": col.primary_key,
                        "comment": col_comment,
                    })
                for c in t.constraints:
                    ref_cols = [c.ref_column] if c.ref_column else []
                    ctype = "PK" if c.type == "PRIMARY KEY" else (
                        "FK" if c.type == "FOREIGN KEY" else c.type
                    )
                    table_obj["constraints"].append({
                        "name": c.name,
                        "type": ctype,
                        "columns": c.columns,
                        "ref_table": c.ref_table or "",
                        "ref_columns": ref_cols,
                        "check_expr": c.check_condition or "",
                    })
                    if c.type == "PRIMARY KEY":
                        table_obj["indexes"].append({
                            "name": c.name,
                            "columns": c.columns,
                            "unique": True,
                        })
                existing_idx_names = {i["name"] for i in table_obj["indexes"]}
                for idx in ddl.indexes:
                    if idx.table_name == t.name and idx.name not in existing_idx_names:
                        table_obj["indexes"].append({
                            "name": idx.name,
                            "columns": idx.columns,
                            "unique": idx.unique,
                        })
                data["tables"].append(table_obj)

            for t in ddl.tables:
                for c in t.constraints:
                    if c.type == "FOREIGN KEY" and c.ref_table:
                        data["edges"].append({
                            "from": t.name,
                            "to": c.ref_table,
                            "label": c.name,
                        })

            for v in ddl.views:
                data["views"].append({
                    "name": v.name,
                    "comment": v.comment or "",
                    "columns": [],
                    "sql": v.sql,
                })

            for pkg in ddl.packages:
                data["packages"].append({
                    "name": pkg.name,
                    "spec": [],
                    "body": [],
                    "body_source": pkg.code,
                    "constants": [],
                    "error_codes": [],
                })

            for seq in ddl.sequences:
                data["sequences"].append({
                    "name": seq.name,
                    "start": seq.start_with or "1",
                    "incr": seq.increment_by or "1",
                    "cache": "NOCACHE",
                })

            for trg in ddl.triggers:
                data["triggers"].append({
                    "name": trg.name,
                    "table": trg.table_name or "",
                })

        for page in app.pages:
            page_obj = self._serialize_page(page)
            data["pages"].append(page_obj)

        data["links"] = self._build_links(app)

        # Top-level shared components
        data["authentications"] = [{
            "name": a.name, "type": a.type or "", "host": a.host or "",
            "port": a.port or "", "use_ssl": a.use_ssl or "", "dn": a.dn_string or "",
        } for a in app.authentications]

        data["plugins"] = [{
            "name": p.name, "internal_name": p.internal_name or "",
            "theme": p.theme or "", "plugin_type": p.plugin_type or "",
            "available_as": p.available_as,
        } for p in app.plugins]

        data["search_configs"] = [{
            "name": s.name, "search_type": s.search_type or "",
            "location": s.location or "", "sql_query": s.sql_query or "",
        } for s in app.search_configs]

        data["data_load_defs"] = [{
            "name": d.name, "target_type": d.target_type or "",
            "table_name": d.table_name or "", "loading_method": d.loading_method or "",
            "commit_interval": d.commit_interval or "",
        } for d in app.data_load_defs]

        data["static_files"] = [{
            "file_name": f.file_name, "mime_type": f.mime_type or "",
        } for f in app.static_files]

        data["page_groups"] = [{"name": g.name} for g in app.page_groups]

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _serialize_page(self, page) -> dict:
        page_obj: dict = {
            "id": page.id,
            "name": page.name,
            "title": page.title or page.name,
            "page_mode": page.page_mode,
            "page_template": page.page_template or "",
            "page_group": page.page_group or "",
            "help_text": page.help_text or "",
            "dialog": page.dialog or {},
            "raw_attributes": {
                "template": page.page_template,
                "template_options": page.template_options,
                "help_text": page.help_text,
                "dialog": page.dialog,
            },
            "computations": [{
                "item_name": comp.item_name,
                "point": comp.point,
                "type": comp.type,
                "language": comp.language or "",
                "code": comp.code or "",
                "build_option": comp.build_option or "",
            } for comp in page.computations],
            "regions": [],
            "items": [],
            "buttons": [],
            "processes": [],
            "dynamic_actions": [],
            "validations": [],
            "branches": [],
            "css_inline": page.css_inline or "",
            "js_inline": page.js_inline or "",
            "javascript_full": page.javascript_full or "",
        }

        for r in page.regions:
            region_obj = {
                "name": r.name,
                "type": r.type,
                "title": r.title or r.name,
                "source_table": r.source_table or "",
                "source_owner": r.source_owner or "",
                "source_sql": r.source_sql or "",
                "source_type": r.source_type or "",
                "source_where": r.source_where or "",
                "html_code": r.html_code or "",
                "page_items_to_submit": r.page_items_to_submit or "",
                "parent_region": r.parent_region or "",
                "editable": r.editable,
                "allowed_operations": r.allowed_operations,
                "lost_update_type": r.lost_update_type or "",
                "template": r.template or "",
                "slot": r.slot or "",
                "sequence": r.sequence,
                "server_side_condition": r.server_side_condition or "",
                "pagination": r.pagination or "",
                "order_by": r.order_by or "",
                "source_location": r.source_location or "",
                "build_option": r.build_option or "",
                "columns": [{
                    "name": col.name,
                    "type": col.type,
                    "heading": col.heading or "",
                    "source_column": col.source_column or "",
                    "primary_key": col.primary_key,
                    "link_target": col.link_target or "",
                    "link_text": col.link_text or "",
                    "link_clear_cache": col.link_clear_cache or "",
                    "master_region": col.master_region or "",
                    "master_column": col.master_column or "",
                    "lov": col.lov or "",
                    "sortable": col.sortable,
                    "column_alignment": col.column_alignment or "",
                    "heading_alignment": col.heading_alignment or "",
                    "sequence": col.sequence,
                    "build_option": col.build_option or "",
                } for col in r.columns],
                "raw_attributes": {
                    "template": r.template,
                    "template_options": r.template_options,
                    "server_side_condition": r.server_side_condition,
                    "pagination": r.pagination,
                    "server_cache": r.server_cache,
                },
            }
            page_obj["regions"].append(region_obj)

        for item in page.items:
            page_obj["items"].append({
                "name": item.name,
                "type": item.type,
                "label": item.label or "",
                "label_alignment": item.label_alignment or "",
                "source_column": item.source_column or "",
                "source_sql": item.source_sql or "",
                "template": item.template or "",
                "width": item.width or "",
                "height": item.height or "",
                "lov": item.lov or "",
                "lov_display_null_value": item.lov_display_null_value or "",
                "lov_display_extra_values": item.lov_display_extra_values or False,
                "default_value": item.default_value or "",
                "data_type": item.data_type or "",
                "storage": item.storage or "",
                "session_state_protection": item.session_state_protection or "",
                "store_encrypted": item.store_encrypted or False,
                "region": item.region or "",
                "slot": item.slot or "",
                "sequence": item.sequence,
                "source_type": item.source_type or "",
                "form_region": item.form_region or "",
                "source_primary_key": item.source_primary_key or False,
                "source_query_only": item.source_query_only or False,
                "value_required": item.value_required or False,
                "validation_max_length": item.validation_max_length,
                "build_option": item.build_option or "",
                "raw_attributes": {
                    "data_type": item.data_type,
                    "storage": item.storage,
                    "session_state_protection": item.session_state_protection,
                    "store_encrypted": item.store_encrypted,
                    "value_protected": item.value_protected,
                },
            })

        for btn in page.buttons:
            page_obj["buttons"].append({
                "name": btn.name,
                "label": btn.label or btn.name,
                "action": btn.action or "",
                "target_page": btn.target_page or "",
                "is_hot": btn.is_hot,
                "region": btn.region or "",
                "slot": btn.slot or "",
                "sequence": btn.sequence,
                "database_action": btn.database_action or "",
                "target_clear_cache": btn.target_clear_cache or "",
                "confirmation_message": btn.confirmation_message or "",
                "confirmation_style": btn.confirmation_style or "",
                "server_side_condition": btn.server_side_condition or "",
                "build_option": btn.build_option or "",
                "raw_attributes": {
                    "is_hot": btn.is_hot,
                    "action": btn.action,
                },
            })

        for proc in page.processes:
            page_obj["processes"].append({
                "name": proc.name,
                "type": proc.type,
                "language": proc.language or "",
                "point": proc.point,
                "code": proc.code or "",
                "condition": proc.condition or "",
                "when_button_pressed": proc.when_button_pressed or "",
                "error_display_location": proc.error_display_location or "",
                "error_message": proc.error_message or "",
                "target_type": proc.target_type or "",
                "return_primary_key_after_insert": proc.return_primary_key_after_insert or False,
                "prevent_lost_updates": proc.prevent_lost_updates or False,
                "lock_row": proc.lock_row or False,
                "success_message": proc.success_message or "",
                "owner": proc.owner or "",
                "package": proc.package or "",
                "procedure_or_function": proc.procedure_or_function or "",
                "build_option": proc.build_option or "",
                "raw_attributes": {
                    "error_display_location": proc.error_display_location,
                    "error_message": proc.error_message,
                    "when_button_pressed": proc.when_button_pressed,
                },
            })

        for da in page.dynamic_actions:
            da_obj = {
                "name": da.name,
                "event": da.event,
                "selection_type": da.selection_type or "",
                "trigger_selector": da.trigger_selector or "",
                "client_side_condition": da.client_side_condition or "",
                "build_option": da.build_option or "",
                "actions": [{
                    "type": step.type,
                    "code": step.code or "",
                    "affected_elements": step.affected_elements or "",
                    "fire_on_initialization": step.fire_on_initialization,
                    "maintain_pagination": step.maintain_pagination or False,
                    "show_processing": step.show_processing or False,
                    "items_to_submit": step.items_to_submit or "",
                    "items_to_return": step.items_to_return or "",
                    "raw_attributes": {},
                } for step in da.actions],
                "raw_attributes": {},
            }
            page_obj["dynamic_actions"].append(da_obj)

        for v in page.validations:
            page_obj["validations"].append({
                "name": v.name,
                "type": v.type,
                "code": v.code or "",
                "condition": v.condition or "",
                "error_message": v.error_message or "",
                "associated_item": v.associated_item or "",
                "build_option": v.build_option or "",
                "raw_attributes": {},
            })

        for b in page.branches:
            page_obj["branches"].append({
                "name": b.name or "",
                "type": b.type,
                "target_page": b.target_page or "",
                "target_url": b.target_url or "",
                "target_values": b.target_values or {},
                "point": b.point,
                "build_option": b.build_option or "",
                "condition": b.condition or "",
                "when_button_pressed": b.when_button_pressed or "",
            })

        return page_obj

    def _build_links(self, app: ApexApp) -> list[dict]:
        links: list[dict] = []
        db_names: set[str] = set()
        if app.ddl_schema:
            for t in app.ddl_schema.tables:
                db_names.add(t.name.upper())
            for v in app.ddl_schema.views:
                db_names.add(v.name.upper())
            for p in app.ddl_schema.packages:
                db_names.add(p.name.upper())

        for page in app.pages:
            page_objects: list[str] = []
            for region in page.regions:
                if region.source_table:
                    self._add_unique(page_objects, region.source_table)
                if region.source_sql:
                    for name in db_names:
                        if name in region.source_sql.upper():
                            orig = self._find_original_name(app, name)
                            if orig:
                                self._add_unique(page_objects, orig)

            for proc in page.processes:
                if proc.code:
                    for name in db_names:
                        if name in proc.code.upper():
                            orig = self._find_original_name(app, name)
                            if orig:
                                self._add_unique(page_objects, orig)

            if page_objects:
                links.append({
                    "page_id": page.id,
                    "page_name": page.name,
                    "objects": page_objects,
                    "source_type": "page",
                    "source_name": page.name,
                })

        return links

    @staticmethod
    def _add_unique(lst: list[str], item: str) -> None:
        if item not in lst:
            lst.append(item)

    def _find_original_name(self, app: ApexApp, upper_name: str) -> str | None:
        if not app.ddl_schema:
            return upper_name
        for t in app.ddl_schema.tables:
            if t.name.upper() == upper_name:
                return t.name
        for v in app.ddl_schema.views:
            if v.name.upper() == upper_name:
                return v.name
        for p in app.ddl_schema.packages:
            if p.name.upper() == upper_name:
                return p.name
        return upper_name

    # ------------------------------------------------------------------
    # CSS
    # ------------------------------------------------------------------
    def _css(self) -> str:
        return """<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       color: #333; background: #f5f5f5; }
header { display: flex; justify-content: space-between; align-items: center;
         padding: 12px 24px; background: #1a365d; color: white; }
.header-left { display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 18px; font-weight: 500; }
.search-box input { padding: 6px 12px; border: none; border-radius: 4px; width: 220px; }
.tabs { display: flex; gap: 0; background: #fff; border-bottom: 2px solid #ddd;
        padding: 0 24px; }
.tab { padding: 10px 20px; border: none; background: none; cursor: pointer;
       font-size: 14px; color: #666; border-bottom: 2px solid transparent; }
.tab.active { color: #1a365d; border-bottom-color: #d4a843; font-weight: 600; }
.tab:hover { color: #1a365d; }
main { padding: 16px 24px; min-height: 70vh; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.detail-panel { background: #fff; border: 1px solid #ddd; border-radius: 4px;
                padding: 16px; margin-top: 12px; max-height: 400px; overflow-y: auto; }
.browser-layout { display: flex; gap: 16px; }
.tree-panel { width: 280px; background: #fff; border: 1px solid #ddd;
              border-radius: 4px; padding: 12px; max-height: 70vh; overflow-y: auto; }
.tree-panel h4 { color: #1a365d; margin: 8px 0 4px; font-size: 13px; }
.tree-item { padding: 4px 8px; cursor: pointer; border-radius: 3px; font-size: 13px; }
.tree-item:hover { background: #e8edf3; }
.tree-item.active { background: #1a365d; color: white; }
.browser-layout .detail-panel { flex: 1; margin-top: 0; max-height: 70vh; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
th { background: #f0f0f0; font-weight: 600; }
.map-layout { display: flex; gap: 16px; align-items: flex-start; }
.map-sidebar { display: flex; flex-direction: column; gap: 12px; width: 320px;
               flex-shrink: 0; }
.map-column { background: #fff; border: 1px solid #ddd; border-radius: 4px;
              padding: 12px; max-height: 35vh; overflow-y: auto; }
.map-column h3 { font-size: 14px; color: #1a365d; margin-bottom: 8px; }
.map-item { padding: 6px 10px; cursor: pointer; border-radius: 3px;
            font-size: 13px; margin: 2px 0; }
.map-item:hover { background: #e8edf3; }
.map-item.highlight { background: #d4a843; color: #1a365d; font-weight: 600; }
.map-item.selected { background: #1a365d; color: white; font-weight: 600; }
.page-detail-panel { flex: 1; background: #fff; border: 1px solid #ddd;
                     border-radius: 4px; padding: 16px; max-height: 80vh;
                     overflow-y: auto; }
.page-detail-placeholder { color: #999; font-style: italic; text-align: center;
                           padding: 40px 20px; }
.page-detail-panel h2 { font-size: 18px; color: #1a365d; margin-bottom: 4px; }
.page-detail-panel .page-meta { color: #666; font-size: 13px; margin-bottom: 16px; }
.section { margin-bottom: 12px; border: 1px solid #e2e8f0; border-radius: 4px; }
.section-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px;
                  background: #f7fafc; cursor: pointer; user-select: none;
                  border-radius: 4px; }
.section-header:hover { background: #edf2f7; }
.section-header h3 { font-size: 14px; color: #1a365d; margin: 0; flex: 1; }
.section-badge { background: #1a365d; color: white; border-radius: 10px;
                 padding: 1px 8px; font-size: 11px; font-weight: 600; }
.section-arrow { font-size: 10px; color: #999; transition: transform 0.2s; }
.section.open .section-arrow { transform: rotate(90deg); }
.section-body { display: none; padding: 12px 14px; border-top: 1px solid #e2e8f0; }
.section.open .section-body { display: block; }
.page-detail-panel pre[class*="language-"] { margin: 8px 0; border-radius: 4px;
    font-size: 12px; max-height: 400px; overflow: auto; }
.page-detail-panel code[class*="language-"] { font-family: "Fira Code", Consolas,
    "Courier New", monospace; font-size: 12px; }
.subsection { margin: 8px 0; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.subsection:last-child { border-bottom: none; }
.subsection-title { font-weight: 600; color: #2d3748; font-size: 13px;
                    margin-bottom: 4px; }
.subsection-meta { font-size: 12px; color: #718096; margin-bottom: 6px; }
.badge { display: inline-block; padding: 1px 6px; border-radius: 3px;
         font-size: 11px; font-weight: 500; margin-right: 4px; }
.badge-type { background: #e2e8f0; color: #4a5568; }
.badge-hot { background: #fed7d7; color: #c53030; }
.badge-point { background: #c6f6d5; color: #276749; }
.badge-event { background: #bee3f8; color: #2b6cb0; }
.badge-trigger { background: #fefcbf; color: #975a16; }
.badge-lang { background: #e9d8fd; color: #6b46c1; }
.badge-pk { background: #fed7d7; color: #c53030; font-weight: 700; }
.badge-link { background: #bee3f8; color: #2b6cb0; }
.db-links-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.db-link-chip { background: #edf2f7; border: 1px solid #cbd5e0; border-radius: 4px;
                padding: 2px 8px; font-size: 12px; color: #2d3748; }
footer { display: flex; justify-content: center; gap: 24px; padding: 16px;
         background: #1a365d; color: #aaa; font-size: 12px; }
footer strong { color: #d4a843; }
pre { background: #f8f8f8; border: 1px solid #ddd; padding: 12px; overflow-x: auto;
      font-size: 12px; border-radius: 4px; }
code { font-family: "Fira Code", Consolas, monospace; }
/* Info tab */
.info-container { max-width: 960px; margin: 0 auto; }
.info-header { text-align: center; padding: 24px 0 16px; border-bottom: 2px solid #d4a843;
               margin-bottom: 24px; }
.info-header h2 { font-size: 24px; color: #1a365d; margin-bottom: 4px; }
.info-subtitle { color: #666; font-size: 14px; }
.info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
             gap: 16px; }
.info-card { background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 16px; }
.info-card h3 { font-size: 15px; color: #1a365d; margin-bottom: 12px;
                padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
.info-table { border: none; margin: 0; }
.info-table td { border: none; padding: 4px 8px; font-size: 13px; }
.info-table td:first-child { color: #666; white-space: nowrap; }
.info-table td:last-child { font-weight: 500; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
              gap: 8px; }
.stat-item { text-align: center; padding: 8px; background: #f7fafc; border-radius: 4px; }
.stat-value { display: block; font-size: 22px; font-weight: 700; color: #1a365d; }
.stat-label { display: block; font-size: 11px; color: #666; margin-top: 2px; }
.badge-yes { background: #c6f6d5; color: #276749; padding: 2px 8px; border-radius: 3px;
             font-size: 12px; font-weight: 600; }
</style>"""

    # ------------------------------------------------------------------
    # JavaScript
    # ------------------------------------------------------------------
    def _app_js(self) -> str:
        return r"""
// === TABS ===
function switchTab(name) {
  document.querySelectorAll(".tab-content").forEach(function(t) {
    t.style.display = "none";
    t.classList.remove("active");
  });
  document.querySelectorAll(".tab").forEach(function(t) { t.classList.remove("active"); });
  var panel = document.getElementById("tab-" + name);
  if (panel) { panel.style.display = "block"; panel.classList.add("active"); }
  if (event && event.target) event.target.classList.add("active");
  if (name === "diagram" && !window._diagramInit) initDiagram();
  if (name === "browser" && !window._browserInit) initBrowser();
  if (name === "map" && !window._mapInit) initMap();
}

// === SEARCH ===
function handleSearch(q) {
  q = q.toLowerCase().trim();
  if (!q) return;
}

// === HELPERS ===
function escapeHtml(s) {
  if (!s) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

function codeBlock(code, lang) {
  return '<pre class="language-' + lang + '"><code class="language-' + lang + '">'
    + escapeHtml(code) + '</code></pre>';
}

function highlightCode(container) {
  if (typeof Prism !== "undefined") {
    container.querySelectorAll("pre code").forEach(function(el) { Prism.highlightElement(el); });
  }
}

function detectLang(code, langHint) {
  if (langHint) {
    var h = langHint.toLowerCase();
    if (h.indexOf("plsql") >= 0 || h.indexOf("pl/sql") >= 0) return "plsql";
    if (h.indexOf("javascript") >= 0 || h.indexOf("js") >= 0) return "javascript";
  }
  if (!code) return "sql";
  var upper = code.toUpperCase();
  if (upper.indexOf("BEGIN") >= 0 || upper.indexOf("DECLARE") >= 0 || upper.indexOf("EXCEPTION") >= 0)
    return "plsql";
  if (code.indexOf("function") >= 0 || code.indexOf("var ") >= 0 || code.indexOf("apex.") >= 0)
    return "javascript";
  return "sql";
}

// === DIAGRAM (vis.js) ===
function initDiagram() {
  window._diagramInit = true;
  if (typeof vis === "undefined") {
    document.getElementById("er-network").innerHTML =
      '<p style="padding:20px;color:#999">vis-network.js nie załadowany (brak internetu?).</p>';
    return;
  }

  function getNodeColor(name) {
    if (name.indexOf("B_SL_") === 0) return { background: "#c6f6d5", border: "#38a169" };
    if (name.indexOf("_HIST") >= 0 || name.indexOf("_TMP") >= 0 || name.indexOf("IMPORT") >= 0)
      return { background: "#e2e8f0", border: "#718096" };
    return { background: "#bee3f8", border: "#3182ce" };
  }

  var nodes = DATA.tables.map(function(t) {
    return {
      id: t.name, label: t.name, shape: "box",
      color: getNodeColor(t.name),
      title: t.comment + " (" + t.columns.length + " kolumn)",
      font: { size: 12 }
    };
  });
  var edges = DATA.edges.map(function(e) {
    return {
      from: e.from, to: e.to, label: e.label,
      arrows: "to", font: { size: 9, align: "middle" },
      color: { color: "#999" }
    };
  });
  var container = document.getElementById("er-network");
  var network = new vis.Network(container,
    { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
    {
      layout: { hierarchical: { direction: "UD", sortMethod: "hubsize", nodeSpacing: 200 } },
      physics: false,
      interaction: { hover: true, dragNodes: true },
      edges: { smooth: { type: "cubicBezier" } }
    }
  );
  network.once("afterDrawing", function() {
    var positions = network.getPositions();
    network.setOptions({
      layout: { hierarchical: { enabled: false } },
      physics: { enabled: false }
    });
    Object.keys(positions).forEach(function(id) {
      network.body.nodes[id].x = positions[id].x;
      network.body.nodes[id].y = positions[id].y;
    });
    network.redraw();
  });
  network.on("click", function(params) {
    if (params.nodes.length) showNodeDetail(params.nodes[0]);
  });
}

function showNodeDetail(name) {
  var t = DATA.tables.find(function(x) { return x.name === name; });
  if (!t) return;
  var html = "<h3>" + escapeHtml(t.name) + "</h3>";
  if (t.comment) html += "<p><em>" + escapeHtml(t.comment) + "</em></p>";
  html += '<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>';
  t.columns.forEach(function(c) {
    html += "<tr><td>" + escapeHtml(c.name) + "</td><td>" + escapeHtml(c.type) + "</td>"
         + "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>"
         + "<td>" + (escapeHtml(c["default"]) || "\u2014") + "</td>"
         + "<td>" + (escapeHtml(c.comment) || "\u2014") + "</td></tr>";
  });
  html += "</table>";
  if (t.constraints.length) {
    html += "<h4>Constraints</h4><ul>";
    t.constraints.forEach(function(c) {
      html += "<li><strong>" + escapeHtml(c.name) + "</strong> [" + c.type + "] "
           + c.columns.join(", ");
      if (c.ref_table) html += " \u2192 " + c.ref_table + "(" + c.ref_columns.join(", ") + ")";
      html += "</li>";
    });
    html += "</ul>";
  }
  document.getElementById("node-detail").innerHTML = html;
}

// === BROWSER ===
function initBrowser() {
  window._browserInit = true;
  var tree = document.getElementById("object-tree");
  var html = "";
  if (DATA.tables.length) {
    html += "<h4>Tabele (" + DATA.tables.length + ")</h4>";
    DATA.tables.forEach(function(t) {
      html += '<div class="tree-item" onclick="showObject(\'table\',\'' + t.name + '\')">' + t.name + '</div>';
    });
  }
  if (DATA.views.length) {
    html += "<h4>Widoki (" + DATA.views.length + ")</h4>";
    DATA.views.forEach(function(v) {
      html += '<div class="tree-item" onclick="showObject(\'view\',\'' + v.name + '\')">' + v.name + '</div>';
    });
  }
  if (DATA.packages.length) {
    html += "<h4>Pakiety (" + DATA.packages.length + ")</h4>";
    DATA.packages.forEach(function(p) {
      html += '<div class="tree-item" onclick="showObject(\'package\',\'' + p.name + '\')">' + p.name + '</div>';
    });
  }
  if (DATA.sequences.length) {
    html += "<h4>Sekwencje (" + DATA.sequences.length + ")</h4>";
    DATA.sequences.forEach(function(s) {
      html += '<div class="tree-item" onclick="showObject(\'sequence\',\'' + s.name + '\')">' + s.name + '</div>';
    });
  }
  tree.innerHTML = html;
}

function showObject(type, name) {
  document.querySelectorAll(".tree-item").forEach(function(e) { e.classList.remove("active"); });
  if (event && event.target) event.target.classList.add("active");
  var panel = document.getElementById("object-detail");
  var html = "";

  if (type === "table") {
    var t = DATA.tables.find(function(x) { return x.name === name; });
    if (!t) return;
    html = "<h3>" + escapeHtml(t.name) + "</h3>";
    if (t.comment) html += "<p><em>" + escapeHtml(t.comment) + "</em></p>";
    html += '<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>';
    t.columns.forEach(function(c) {
      html += "<tr><td>" + escapeHtml(c.name) + "</td><td>" + escapeHtml(c.type) + "</td>"
           + "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>"
           + "<td>" + (escapeHtml(c["default"]) || "\u2014") + "</td>"
           + "<td>" + (escapeHtml(c.comment) || "\u2014") + "</td></tr>";
    });
    html += "</table>";
    if (t.constraints.length) {
      html += "<h4>Constraints</h4><ul>";
      t.constraints.forEach(function(c) {
        html += "<li><strong>" + escapeHtml(c.name) + "</strong> [" + c.type + "] "
             + c.columns.join(", ");
        if (c.ref_table) html += " \u2192 " + c.ref_table;
        html += "</li>";
      });
      html += "</ul>";
    }
  } else if (type === "view") {
    var v = DATA.views.find(function(x) { return x.name === name; });
    if (!v) return;
    html = "<h3>" + escapeHtml(v.name) + "</h3>";
    if (v.comment) html += "<p><em>" + escapeHtml(v.comment) + "</em></p>";
    if (v.sql) html += codeBlock(v.sql, "sql");
  } else if (type === "package") {
    var p = DATA.packages.find(function(x) { return x.name === name; });
    if (!p) return;
    html = "<h3>" + escapeHtml(p.name) + "</h3>";
    if (p.body_source) html += codeBlock(p.body_source, "plsql");
  } else if (type === "sequence") {
    var s = DATA.sequences.find(function(x) { return x.name === name; });
    if (!s) return;
    html = "<h3>" + escapeHtml(s.name) + "</h3>";
    html += "<p>Start: " + s.start + " | Increment: " + s.incr + " | Cache: " + s.cache + "</p>";
  }

  panel.innerHTML = html;
  highlightCode(panel);
}

// === MAP ===
function initMap() {
  window._mapInit = true;
  var pageList = document.getElementById("page-list");
  var dbList = document.getElementById("db-list");
  var pHtml = "";
  DATA.pages.forEach(function(p) {
    pHtml += '<div class="map-item" data-page="' + p.id + '" onclick="selectPage(' + p.id + ')">' +
             'Strona ' + p.id + ': ' + escapeHtml(p.name) + '</div>';
  });
  pageList.innerHTML = pHtml;
  var dHtml = "";
  var allObjects = DATA.tables.map(function(t){return t.name;})
    .concat(DATA.views.map(function(v){return v.name;}));
  allObjects.forEach(function(n) {
    dHtml += '<div class="map-item" data-obj="' + n + '" onclick="highlightFromObject(\'' + n + '\')">' + n + '</div>';
  });
  dbList.innerHTML = dHtml;
}

function selectPage(pageId) {
  clearHighlights();
  document.querySelectorAll("[data-page]").forEach(function(e) { e.classList.remove("selected"); });
  document.querySelectorAll('[data-page="' + pageId + '"]').forEach(function(e) { e.classList.add("selected"); });
  var linked = DATA.links.filter(function(l) { return l.page_id === pageId; });
  var objects = {};
  linked.forEach(function(l) { l.objects.forEach(function(o) { objects[o] = true; }); });
  Object.keys(objects).forEach(function(o) {
    document.querySelectorAll('[data-obj="' + o + '"]').forEach(function(e) { e.classList.add("highlight"); });
  });
  showPageDetail(pageId);
}

function highlightFromObject(name) {
  clearHighlights();
  document.querySelectorAll("[data-page]").forEach(function(e) { e.classList.remove("selected"); });
  var linked = DATA.links.filter(function(l) { return l.objects.indexOf(name) >= 0; });
  var pages = {};
  linked.forEach(function(l) { pages[l.page_id] = true; });
  document.querySelectorAll('[data-obj="' + name + '"]').forEach(function(e) { e.classList.add("highlight"); });
  Object.keys(pages).forEach(function(p) {
    document.querySelectorAll('[data-page="' + p + '"]').forEach(function(e) { e.classList.add("highlight"); });
  });
}

function clearHighlights() {
  document.querySelectorAll(".map-item").forEach(function(e) { e.classList.remove("highlight"); });
}

// === PAGE DETAIL ===
function showPageDetail(pageId) {
  var page = DATA.pages.find(function(p) { return p.id === pageId; });
  if (!page) return;
  var panel = document.getElementById("page-detail-panel");
  var html = "<h2>Strona " + page.id + ": " + escapeHtml(page.name) + "</h2>";
  html += '<div class="page-meta">';
  if (page.title && page.title !== page.name) html += "Tytu\u0142: " + escapeHtml(page.title) + " | ";
  html += "Tryb: " + page.page_mode;
  if (page.page_template) html += " | Szablon: " + escapeHtml(page.page_template);
  if (page.page_group) html += " | Grupa: " + escapeHtml(page.page_group);
  html += "</div>";
  if (page.help_text) {
    html += '<div style="background:#f7fafc;border-left:3px solid #1a365d;padding:8px 12px;margin-bottom:12px;font-size:13px"><strong>Pomoc:</strong> ' + escapeHtml(page.help_text) + '</div>';
  }

  var linked = DATA.links.filter(function(l) { return l.page_id === pageId; });
  if (linked.length) {
    var dbObjs = {};
    linked.forEach(function(l) { l.objects.forEach(function(o) { dbObjs[o] = true; }); });
    html += '<div class="db-links-list" style="margin-bottom:12px">';
    Object.keys(dbObjs).forEach(function(o) { html += '<span class="db-link-chip">' + o + '</span>'; });
    html += "</div>";
  }

  if (page.computations && page.computations.length)
    html += section("Komputacje strony", page.computations.length, renderComputations(page.computations));
  if (page.regions.length)
    html += section("Regiony", page.regions.length, renderRegions(page.regions), true);
  if (page.items.length)
    html += section("Elementy formularza", page.items.length, renderItems(page.items));
  if (page.buttons.length)
    html += section("Przyciski", page.buttons.length, renderButtons(page.buttons));
  if (page.processes.length)
    html += section("Procesy", page.processes.length, renderProcesses(page.processes));
  if (page.dynamic_actions.length)
    html += section("Dynamic Actions", page.dynamic_actions.length, renderDynamicActions(page.dynamic_actions));
  if (page.validations.length)
    html += section("Walidacje", page.validations.length, renderValidations(page.validations));
  if (page.branches.length)
    html += section("Branching", page.branches.length, renderBranches(page.branches));
  if (page.css_inline)
    html += section("Inline CSS", null, codeBlock(page.css_inline, "css"));
  if (page.javascript_full)
    html += section("JS (Deklaracje)", null, codeBlock(page.javascript_full, "javascript"));
  if (page.js_inline)
    html += section("Inline JavaScript", null, codeBlock(page.js_inline, "javascript"));

  panel.innerHTML = html;
  highlightCode(panel);

  var firstSection = panel.querySelector(".section");
  if (firstSection) firstSection.classList.add("open");
}

function section(title, count, bodyHtml, openByDefault) {
  var badge = count !== null && count !== undefined ? ' <span class="section-badge">' + count + '</span>' : "";
  return '<div class="section' + (openByDefault ? ' open' : '') + '">' +
    '<div class="section-header" onclick="this.parentElement.classList.toggle(\'open\')">' +
    '<span class="section-arrow">\u25B6</span>' +
    '<h3>' + title + badge + '</h3></div>' +
    '<div class="section-body">' + bodyHtml + '</div></div>';
}

function boBadge(bo) {
  if (!bo) return '';
  return ' <span class="badge badge-hot">\u26a0 ' + escapeHtml(bo) + '</span>';
}

function renderComputations(comps) {
  var html = "";
  comps.forEach(function(c) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(c.item_name) + boBadge(c.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    if (c.point) html += '<span class="badge badge-point">' + escapeHtml(c.point) + '</span>';
    if (c.type) html += ' <span class="badge badge-type">' + escapeHtml(c.type) + '</span>';
    if (c.language) html += ' <span class="badge badge-lang">' + escapeHtml(c.language) + '</span>';
    html += '</div>';
    if (c.code) html += codeBlock(c.code, detectLang(c.code, c.language));
    html += '</div>';
  });
  return html;
}

function renderRegions(regions) {
  var html = "";
  regions.forEach(function(r) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(r.title || r.name) + boBadge(r.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    html += '<span class="badge badge-type">' + r.type + '</span>';
    if (r.source_table) html += ' \u2190 tabela: <strong>' + escapeHtml((r.source_owner ? r.source_owner + "." : "") + r.source_table) + '</strong>';
    if (r.editable) html += ' <span class="badge badge-hot">edytowalny</span>';
    if (r.allowed_operations && r.allowed_operations.length) html += ' [' + r.allowed_operations.join(', ') + ']';
    if (r.lost_update_type) html += ' | konflikt aktualizacji: ' + escapeHtml(r.lost_update_type);
    if (r.source_where) html += ' | filtr: <code>' + escapeHtml(r.source_where) + '</code>';
    if (r.page_items_to_submit) html += ' | przesyła: ' + escapeHtml(r.page_items_to_submit);
    if (r.parent_region) html += ' | region nadrz\u0119dny: ' + r.parent_region;
    if (r.server_side_condition) html += ' | warunek: <code>' + escapeHtml(r.server_side_condition) + '</code>';
    if (r.pagination) html += ' | paginacja: ' + escapeHtml(r.pagination);
    html += '</div>';
    if (r.source_sql) html += codeBlock(r.source_sql, "sql");
    if (r.html_code) html += codeBlock(r.html_code, "html");
    if (r.columns.length) {
      html += '<table><tr><th>Kolumna</th><th>Typ</th><th>Nag\u0142\u00f3wek</th><th>\u0179r\u00f3d\u0142o</th><th>Info</th></tr>';
      r.columns.forEach(function(c) {
        var info = "";
        if (c.primary_key) info += '<span class="badge badge-pk">PK</span> ';
        if (c.sortable) info += '<span class="badge badge-type">sort</span> ';
        if (c.column_alignment) info += '<span class="badge badge-type">' + escapeHtml(c.column_alignment) + '</span> ';
        if (c.link_target) info += '<span class="badge badge-link">\u2192 str.' + c.link_target + '</span> ';
        if (c.link_text) info += 'link: ' + escapeHtml(c.link_text) + ' ';
        if (c.master_region || c.master_column) info += 'master: ' + escapeHtml((c.master_region || "?") + "." + (c.master_column || "?")) + ' ';
        if (c.lov) info += "LOV: " + c.lov + " ";
        if (c.build_option) info += boBadge(c.build_option);
        html += "<tr><td>" + escapeHtml(c.name) + "</td><td>" + escapeHtml(c.type) + "</td>" +
          "<td>" + (escapeHtml(c.heading) || "\u2014") + "</td>" +
          "<td>" + (escapeHtml(c.source_column) || "\u2014") + "</td>" +
          "<td>" + (info || "\u2014") + "</td></tr>";
      });
      html += "</table>";
    }
    html += "</div>";
  });
  return html;
}

function renderItems(items) {
  var html = '<table><tr><th>Nazwa</th><th>Typ</th><th>Label</th><th>Kolumna</th><th>LOV</th><th>Ochrona / Storage</th></tr>';
  items.forEach(function(it) {
    var info = [];
    if (it.data_type) info.push(escapeHtml(it.data_type));
    if (it.session_state_protection) info.push(escapeHtml(it.session_state_protection));
    if (it.storage) info.push(escapeHtml(it.storage));
    if (it.value_required) info.push("wymagane");
    if (it.validation_max_length) info.push("max. " + it.validation_max_length);
    if (it.form_region) info.push("formularz: " + escapeHtml(it.form_region));
    if (it.source_primary_key) info.push("PK");
    if (it.source_query_only) info.push("tylko odczyt");
    if (it.lov_display_null_value) info.push("pusta: " + escapeHtml(it.lov_display_null_value));
    if (it.lov_display_extra_values) info.push("LOV rozszerzalny");
    var nameCol = escapeHtml(it.name) + boBadge(it.build_option);
    html += "<tr><td>" + nameCol + "</td><td>" + escapeHtml(it.type) + "</td>" +
      "<td>" + (escapeHtml(it.label) || "\u2014") + "</td>" +
      "<td>" + (escapeHtml(it.source_column) || "\u2014") + "</td>" +
      "<td>" + (escapeHtml(it.lov) || "\u2014") + "</td>" +
      "<td>" + (info.join(" | ") || "\u2014") + "</td></tr>";
  });
  return html + "</table>";
}

function renderButtons(buttons) {
  var html = "";
  buttons.forEach(function(b) {
    html += '<div class="subsection">';
    html += '<span class="subsection-title">' + escapeHtml(b.name) + boBadge(b.build_option) + '</span>';
    if (b.is_hot) html += ' <span class="badge badge-hot">PRIMARY</span>';
    html += '<div class="subsection-meta">';
    html += 'Label: <strong>' + escapeHtml(b.label || b.name) + '</strong>';
    if (b.action) html += ' | Akcja: ' + escapeHtml(b.action);
    if (b.target_page) html += ' | \u2192 Strona ' + b.target_page;
    if (b.database_action) html += ' | DML: ' + escapeHtml(b.database_action);
    if (b.region) html += ' | region: ' + escapeHtml(b.region);
    if (b.slot) html += ' | slot: ' + escapeHtml(b.slot);
    if (b.target_clear_cache) html += ' | czyści cache: <code>' + escapeHtml(b.target_clear_cache) + '</code>';
    if (b.confirmation_message) html += ' | Potwierdzenie: ' + escapeHtml(b.confirmation_message);
    if (b.server_side_condition) html += ' | warunek: <code>' + escapeHtml(b.server_side_condition) + '</code>';
    html += '</div></div>';
  });
  return html;
}

function renderProcesses(processes) {
  var html = "";
  processes.forEach(function(pr) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(pr.name) + boBadge(pr.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    html += '<span class="badge badge-type">' + escapeHtml(pr.type) + '</span>';
    if (pr.language) html += ' <span class="badge badge-lang">' + escapeHtml(pr.language) + '</span>';
    html += ' <span class="badge badge-point">' + escapeHtml(pr.point) + '</span>';
    if (pr.when_button_pressed) html += ' | przycisk: <strong>' + escapeHtml(pr.when_button_pressed) + '</strong>';
    if (pr.condition) html += ' | warunek: <code>' + escapeHtml(pr.condition) + '</code>';
    if (pr.error_display_location) html += ' | b\u0142\u0105d: ' + escapeHtml(pr.error_display_location);
    if (pr.target_type) html += ' | operacja: ' + escapeHtml(pr.target_type);
    if (pr.return_primary_key_after_insert) html += ' | zwraca PK';
    if (pr.prevent_lost_updates) html += ' | kontrola lost update';
    if (pr.lock_row) html += ' | blokada wiersza';
    if (pr.success_message) html += ' | sukces: ' + escapeHtml(pr.success_message);
    if (pr.package || pr.procedure_or_function) html += ' | wywołanie: <code>' + escapeHtml((pr.owner ? pr.owner + "." : "") + (pr.package || "?") + "." + (pr.procedure_or_function || "?")) + '</code>';
    html += '</div>';
    if (pr.code) {
      var lang = detectLang(pr.code, pr.language);
      html += codeBlock(pr.code, lang);
    }
    html += '</div>';
  });
  return html;
}

function renderDynamicActions(das) {
  var html = "";
  das.forEach(function(da) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(da.name) + boBadge(da.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    html += '<span class="badge badge-event">' + escapeHtml(da.event) + '</span>';
    if (da.selection_type) html += ' <span class="badge badge-trigger">' + escapeHtml(da.selection_type) + '</span>';
    if (da.trigger_selector) html += ' \u2192 ' + escapeHtml(da.trigger_selector);
    if (da.client_side_condition) html += ' | warunek JS: <code>' + escapeHtml(da.client_side_condition) + '</code>';
    html += '</div>';
    if (da.actions.length) {
      da.actions.forEach(function(step, i) {
        html += '<div style="margin-left:16px;margin-top:6px">';
        html += '<strong>Krok ' + (i+1) + ':</strong> ' + escapeHtml(step.type);
        if (step.affected_elements) html += ' \u2192 ' + escapeHtml(step.affected_elements);
        if (step.fire_on_initialization) html += ' <span class="badge badge-point">init</span>';
        if (step.maintain_pagination) html += ' | zachowuje paginację';
        if (step.items_to_submit) html += ' | przesyła: ' + escapeHtml(step.items_to_submit);
        if (step.items_to_return) html += ' | odbiera: ' + escapeHtml(step.items_to_return);
        if (step.code) {
          var lang = detectLang(step.code, step.type);
          html += codeBlock(step.code, lang);
        }
        html += '</div>';
      });
    }
    html += '</div>';
  });
  return html;
}

function renderValidations(validations) {
  var html = "";
  validations.forEach(function(v) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(v.name) + boBadge(v.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    html += '<span class="badge badge-type">' + escapeHtml(v.type) + '</span>';
    if (v.associated_item) html += ' | item: ' + escapeHtml(v.associated_item);
    if (v.error_message) html += ' | błąd: ' + escapeHtml(v.error_message);
    if (v.condition) html += ' | warunek: ' + escapeHtml(v.condition);
    html += '</div>';
    if (v.code) html += codeBlock(v.code, detectLang(v.code));
    html += '</div>';
  });
  return html;
}

function renderBranches(branches) {
  var html = "";
  branches.forEach(function(b) {
    html += '<div class="subsection">';
    html += '<div class="subsection-title">' + escapeHtml(b.name || "Branch") + boBadge(b.build_option) + '</div>';
    html += '<div class="subsection-meta">';
    html += '<span class="badge badge-type">' + escapeHtml(b.type) + '</span>';
    html += ' <span class="badge badge-point">' + escapeHtml(b.point) + '</span>';
    if (b.target_page) html += ' | \u2192 Strona ' + b.target_page;
    if (b.target_url) html += ' | URL: ' + escapeHtml(b.target_url);
    if (b.when_button_pressed) html += ' | przycisk: <strong>' + escapeHtml(b.when_button_pressed) + '</strong>';
    if (b.target_values && Object.keys(b.target_values).length) {
      var vals = Object.keys(b.target_values).map(function(k){ return k + "=" + b.target_values[k]; }).join(", ");
      html += ' | parametry: ' + escapeHtml(vals);
    }
    if (b.condition) html += ' | warunek: ' + escapeHtml(b.condition);
    html += '</div></div>';
  });
  return html;
}

// === INIT ===
document.addEventListener("DOMContentLoaded", function() {
  initDiagram();
});
"""
