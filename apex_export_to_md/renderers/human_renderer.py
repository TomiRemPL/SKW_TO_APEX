"""Human Renderer — generuje czytelny Markdown z modelu APEX.

Format wyjściowy: nagłówki, tabele, bloki kodu — czytelny dla człowieka.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, Computation, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
    Authentication, Plugin, SearchConfig, DataLoadDef, StaticFile, PageGroup,
    DDLSchema, DDLTable, DDLView, DDLPackage, DDLProcedure, DDLSequence,
    AppMetadata,
)


def _bo_suffix(bo: str | None) -> str:
    if not bo:
        return ""
    if bo == "Commented Out":
        return " `[ZAKOMENTOWANY]`"
    return f" `[Wyłączony: {bo}]`"


class HumanRenderer(BaseRenderer):
    """Renderer Markdown czytelny dla człowieka."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny dokument Markdown."""
        lines: list[str] = []

        # Timestamp generowania
        if self._timestamp:
            lines.append(f"<!-- Generated: {self._timestamp} -->")
            lines.append("")

        # Nagłówek aplikacji
        lines.append(f"# Aplikacja {app.name} (ID: {app.id}, alias: {app.alias})")
        lines.append("")

        # Metadane aplikacji (z pliku f*.sql)
        if app.metadata:
            lines.extend(self._render_metadata(app.metadata))

        # Strony
        if app.pages:
            lines.append("## Strony użytkownika")
            lines.append("")
            for page in app.pages:
                lines.extend(self._render_page(page))

        # Shared components
        if self._config.include_shared_components:
            sc_lines = self._render_shared_components(app)
            if sc_lines:
                lines.append("---")
                lines.append("")
                lines.extend(sc_lines)

        return "\n".join(lines)

    def _render_metadata(self, meta: AppMetadata) -> list[str]:
        """Renderuj sekcję metadanych aplikacji."""
        lines: list[str] = []
        lines.append("## Informacje o aplikacji")
        lines.append("")
        lines.append(f"| Parametr | Wartość |")
        lines.append(f"|----------|---------|")
        if meta.app_name:
            lines.append(f"| Nazwa | {meta.app_name} |")
        if meta.app_id:
            lines.append(f"| ID aplikacji | {meta.app_id} |")
        if meta.alias:
            lines.append(f"| Alias | {meta.alias} |")
        if meta.version:
            lines.append(f"| Wersja | {meta.version} |")
        if meta.apex_version:
            lines.append(f"| Wersja APEX | {meta.apex_version} |")
        if meta.owner:
            lines.append(f"| Schemat (owner) | {meta.owner} |")
        if meta.language:
            lines.append(f"| Język | {meta.language} |")
        if meta.exported_by:
            lines.append(f"| Eksportowane przez | {meta.exported_by} |")
        if meta.copyright:
            lines.append(f"| Copyright | {meta.copyright} |")
        if meta.is_pwa:
            pwa_info = "Tak"
            if meta.pwa_installable:
                pwa_info += " (installable)"
            if meta.push_enabled:
                pwa_info += " + Push"
            lines.append(f"| PWA | {pwa_info} |")
        lines.append("")

        settings = [
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
        settings = [(label, value) for label, value in settings if value]
        if settings:
            lines.append("### Konfiguracja techniczna")
            lines.append("")
            lines.append("| Parametr | Wartość |")
            lines.append("|----------|---------|")
            for label, value in settings:
                lines.append(f"| {label} | {value} |")
            lines.append("")

        # Statystyki
        lines.append("### Statystyki eksportu")
        lines.append("")
        lines.append("| Komponent | Ilość |")
        lines.append("|-----------|-------|")
        if meta.pages_count:
            lines.append(f"| Strony | {meta.pages_count} |")
        if meta.regions_count:
            lines.append(f"| Regiony | {meta.regions_count} |")
        if meta.items_count:
            lines.append(f"| Elementy (Items) | {meta.items_count} |")
        if meta.buttons_count:
            lines.append(f"| Przyciski | {meta.buttons_count} |")
        if meta.processes_count:
            lines.append(f"| Procesy | {meta.processes_count} |")
        if meta.dynamic_actions_count:
            lines.append(f"| Akcje dynamiczne | {meta.dynamic_actions_count} |")
        if meta.validations_count:
            lines.append(f"| Walidacje | {meta.validations_count} |")
        if meta.lovs_count:
            lines.append(f"| LOV | {meta.lovs_count} |")
        if meta.build_options_count:
            lines.append(f"| Build Options | {meta.build_options_count} |")
        if meta.lists_count:
            lines.append(f"| Listy nawigacyjne | {meta.lists_count} |")
        lines.append("")

        # Zmienne substytucyjne
        if meta.substitutions:
            lines.append("### Zmienne substytucyjne")
            lines.append("")
            lines.append("| Nazwa | Wartość |")
            lines.append("|-------|---------|")
            for key, val in meta.substitutions.items():
                lines.append(f"| {key} | {val} |")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _render_page(self, page: ApexPage) -> list[str]:
        """Renderuj pojedynczą stronę."""
        lines: list[str] = []
        lines.append(f"### Strona {page.id}: {page.name}")
        if page.title and page.title != page.name:
            lines.append(f"- **Tytuł:** {page.title}")
        lines.append(f"- **Tryb:** {page.page_mode}")
        if page.page_template:
            lines.append(f"- **Szablon:** {page.page_template}")
        if page.page_group:
            lines.append(f"- **Grupa stron:** {page.page_group}")
        if page.help_text:
            lines.append(f"- **Pomoc:** {page.help_text}")
        if page.dialog:
            dialog_info = ", ".join(f"{k}: {v}" for k, v in page.dialog.items())
            lines.append(f"- **Ustawienia dialogu:** {dialog_info}")
        if page.security:
            auth = page.security.get("authentication", "")
            if auth:
                lines.append(f"- **Uwierzytelnianie:** {auth}")
        lines.append("")

        # Komputacje strony
        if page.computations:
            lines.append("#### Komputacje strony")
            lines.append("")
            for comp in page.computations:
                point_info = f" ({comp.point})" if comp.point else ""
                type_info = f" [{comp.type}]" if comp.type else ""
                lines.append(f"- **{comp.item_name}**{_bo_suffix(comp.build_option)}{point_info}{type_info}")
                if comp.code and self._should_include_code():
                    lines.append("  ```plsql")
                    lines.append(f"  {comp.code}")
                    lines.append("  ```")
            lines.append("")

        # Regiony
        for region in page.regions:
            lines.extend(self._render_region(region))

        # Elementy formularza
        if page.items:
            lines.append("#### Elementy formularza")
            lines.append("")
            lines.append("| Nazwa | Typ | Etykieta | Kolumna | LOV | Walidacja | Źródło |")
            lines.append("|-------|-----|----------|---------|-----|-----------|--------|")
            for item in page.items:
                validation: list[str] = []
                if item.value_required:
                    validation.append("wymagane")
                if item.validation_max_length:
                    validation.append(f"max. {item.validation_max_length}")
                source: list[str] = []
                if item.form_region:
                    source.append(f"formularz: {item.form_region}")
                if item.source_primary_key:
                    source.append("PK")
                if item.source_query_only:
                    source.append("tylko odczyt")
                lines.append(
                    f"| {item.name}{_bo_suffix(item.build_option)} | {item.type} "
                    f"| {item.label or '—'} | {item.source_column or '—'} "
                    f"| {item.lov or '—'} | {', '.join(validation) or '—'} | {', '.join(source) or '—'} |"
                )
                if item.lov_display_null_value or item.lov_display_extra_values:
                    lov_info: list[str] = []
                    if item.lov_display_null_value:
                        lov_info.append(f"pusta wartość: {item.lov_display_null_value}")
                    if item.lov_display_extra_values:
                        lov_info.append("dopuszcza wartości spoza LOV")
                    lines.append(f"| ↳ | | | | | | {', '.join(lov_info)} |")
                if item.template or item.width or item.height or item.source_sql:
                    extra: list[str] = []
                    if item.template:
                        extra.append(f"sablon: {item.template}")
                    if item.width:
                        extra.append(f"szer: {item.width}")
                    if item.height:
                        extra.append(f"wys: {item.height}")
                    if item.source_sql:
                        extra.append("SQL")
                    lines.append(f"| ↳ | | | | | | {', '.join(extra)} |")
                    if item.source_sql and self._should_include_code():
                        lines.append("  ```sql")
                        lines.append(f"  {item.source_sql}")
                        lines.append("  ```")
            lines.append("")

        # Przyciski
        if page.buttons:
            lines.append("#### Przyciski")
            lines.append("")
            for btn in page.buttons:
                hot = " **(primary)**" if btn.is_hot else ""
                target = f" → strona {btn.target_page}" if btn.target_page else ""
                db_act = f" [DML: {btn.database_action}]" if btn.database_action else ""
                lines.append(f"- **{btn.name}**{_bo_suffix(btn.build_option)} — {btn.label or '?'} [{btn.action or '?'}]{hot}{target}{db_act}")
                if btn.region or btn.slot or btn.sequence is not None:
                    loc_parts: list[str] = []
                    if btn.region:
                        loc_parts.append(f"region: {btn.region}")
                    if btn.slot:
                        loc_parts.append(f"slot: {btn.slot}")
                    if btn.sequence is not None:
                        loc_parts.append(f"kolejność: {btn.sequence}")
                    lines.append(f"  - Lokalizacja: {', '.join(loc_parts)}")
                if btn.target_clear_cache:
                    lines.append(f"  - Czyści cache: `{btn.target_clear_cache}`")
                if btn.confirmation_message:
                    style = f" (styl: {btn.confirmation_style})" if btn.confirmation_style else ""
                    lines.append(f"  - Potwierdzenie: {btn.confirmation_message}{style}")
                if btn.server_side_condition:
                    lines.append(f"  - Warunek serwerowy: `{btn.server_side_condition}`")
            lines.append("")

        # Procesy
        if page.processes:
            lines.append("#### Procesy")
            lines.append("")
            for proc in page.processes:
                btn_info = f", przycisk: {proc.when_button_pressed}" if proc.when_button_pressed else ""
                lang_info = f", język: {proc.language}" if proc.language else ""
                err_info = f", błąd: {proc.error_display_location}" if proc.error_display_location else ""
                lines.append(f"**{proc.name}**{_bo_suffix(proc.build_option)} ({proc.point}{lang_info}{btn_info}{err_info})")
                if proc.condition:
                    lines.append(f"- Warunek: `{proc.condition}`")
                if proc.target_type:
                    lines.append(f"- Operacja docelowa: {proc.target_type}")
                process_flags: list[str] = []
                if proc.return_primary_key_after_insert:
                    process_flags.append("zwraca PK po insercie")
                if proc.prevent_lost_updates:
                    process_flags.append("zapobiega lost update")
                if proc.lock_row:
                    process_flags.append("blokuje wiersz")
                if process_flags:
                    lines.append(f"- Ustawienia DML: {', '.join(process_flags)}")
                if proc.success_message:
                    lines.append(f"- Komunikat sukcesu: {proc.success_message}")
                if proc.error_message:
                    lines.append(f"- Komunikat błędu: {proc.error_message}")
                if proc.package or proc.procedure_or_function:
                    owner = f"{proc.owner}." if proc.owner else ""
                    lines.append(f"- Wywołanie: `{owner}{proc.package or '?'}.{proc.procedure_or_function or '?'}`")
                lines.append("")
                if proc.code and self._should_include_code():
                    lang_hint = (proc.language or "sql").lower().replace("/", "")
                    lines.append(f"```{lang_hint}")
                    lines.append(proc.code)
                    lines.append("```")
                    lines.append("")
                elif proc.code and self._should_summarize_code():
                    first_line = proc.code.strip().split("\n")[0]
                    lines.append(f"> `{first_line}...`")
                    lines.append("")

        # Akcje dynamiczne
        if page.dynamic_actions:
            lines.append("#### Akcje dynamiczne")
            lines.append("")
            for da in page.dynamic_actions:
                trigger_info = f" na {da.selection_type}: {da.trigger_selector}" if da.trigger_selector else ""
                lines.append(f"- **{da.name}**{_bo_suffix(da.build_option)} — zdarzenie: {da.event}{trigger_info}")
                if da.client_side_condition:
                    lines.append(f"  - Warunek JavaScript: `{da.client_side_condition}`")
                for step in da.actions:
                    init_str = " (on init)" if step.fire_on_initialization else ""
                    lines.append(f"  - Krok: {step.type}{init_str}")
                    if step.affected_elements:
                        lines.append(f"    - Wpływa na: {step.affected_elements}")
                    if step.maintain_pagination:
                        lines.append("    - Zachowuje paginację")
                    if step.items_to_submit:
                        lines.append(f"    - Przesyła elementy: {step.items_to_submit}")
                    if step.items_to_return:
                        lines.append(f"    - Odbiera elementy: {step.items_to_return}")
                    if step.code and self._should_include_code():
                        lines.append(f"    ```")
                        lines.append(f"    {step.code}")
                        lines.append(f"    ```")
            lines.append("")

        # Rozgałęzienia
        if page.branches:
            lines.append("#### Rozgałęzienia")
            lines.append("")
            for branch in page.branches:
                target = f"strona {branch.target_page}" if branch.target_page else branch.target_url or "?"
                cond = f" (warunek: {branch.condition})" if branch.condition else ""
                btn_info = f" (przycisk: {branch.when_button_pressed})" if branch.when_button_pressed else ""
                lines.append(f"- {branch.name or '?'}{_bo_suffix(branch.build_option)} → {target}{cond}{btn_info}")
                if branch.target_values:
                    vals = ", ".join(f"{k}={v}" for k, v in branch.target_values.items())
                    lines.append(f"  - Parametry URL: `{vals}`")
            lines.append("")

        # Walidacje
        if page.validations:
            lines.append("#### Walidacje")
            lines.append("")
            for val in page.validations:
                cond = f" (warunek: {val.condition})" if val.condition else ""
                item_info = f" [{val.associated_item}]" if val.associated_item else ""
                lines.append(f"- **{val.name}**{_bo_suffix(val.build_option)} — typ: {val.type}{item_info}{cond}")
                if val.error_message:
                    lines.append(f"  - Komunikat błędu: {val.error_message}")
                if val.code and self._should_include_code():
                    lines.append(f"  ```plsql")
                    lines.append(f"  {val.code}")
                    lines.append(f"  ```")
            lines.append("")

        # CSS/JS
        if page.css_inline:
            lines.append("#### CSS strony")
            lines.append("")
            lines.append("```css")
            lines.append(page.css_inline)
            lines.append("```")
            lines.append("")

        if page.javascript_full:
            lines.append("#### JavaScript — deklaracje funkcji/zmiennych")
            lines.append("")
            lines.append("```javascript")
            lines.append(page.javascript_full)
            lines.append("```")
            lines.append("")

        if page.js_inline:
            lines.append("#### JavaScript strony (execute on load)")
            lines.append("")
            lines.append("```javascript")
            lines.append(page.js_inline)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _render_region(self, region: Region) -> list[str]:
        """Renderuj region z kolumnami."""
        lines: list[str] = []
        title_part = f' — "{region.title}"' if region.title else ""
        lines.append(f"#### Region: {region.name}{_bo_suffix(region.build_option)}{title_part}")

        # Typ i źródło
        type_info = region.type
        if region.source_type and region.source_type not in type_info:
            type_info += f" ({region.source_type})"
        if region.editable:
            ops = ", ".join(region.allowed_operations) if region.allowed_operations else "?"
            type_info += f" (edytowalny: {ops})"

        lines.append(f"- **Typ:** {type_info}")
        if region.template:
            lines.append(f"- **Szablon:** {region.template}")
        if region.slot:
            lines.append(f"- **Slot:** {region.slot}")
        if region.source_table:
            owner = f"{region.source_owner}." if region.source_owner else ""
            lines.append(f"- **Źródło:** tabela `{owner}{region.source_table}`")
        if region.source_where:
            lines.append(f"- **Warunek źródła:** `{region.source_where}`")
        if region.page_items_to_submit:
            lines.append(f"- **Elementy przekazywane do źródła:** {region.page_items_to_submit}")
        if region.lost_update_type:
            lines.append(f"- **Strategia konfliktu aktualizacji:** {region.lost_update_type}")
        if region.server_side_condition:
            lines.append(f"- **Warunek serwerowy:** `{region.server_side_condition}`")
        if region.pagination:
            lines.append(f"- **Paginacja:** {region.pagination}")
        if region.source_sql:
            lines.append(f"- **Źródło SQL:**")
            if self._should_include_code():
                lines.append(f"```sql")
                lines.append(region.source_sql)
                lines.append(f"```")
        if region.html_code:
            lines.append(f"- **Zawartość HTML:**")
            if self._should_include_code():
                lines.append(f"```html")
                lines.append(region.html_code)
                lines.append(f"```")
            elif self._should_summarize_code():
                first_line = region.html_code.strip().split("\n")[0]
                lines.append(f"> `{first_line}...`")
        lines.append("")

        # Kolumny jako tabela
        if region.columns:
            lines.append("| Kolumna | Typ | Nagłówek | Źródło | PK | Link / relacja | Sortowalne | Wyrównanie |")
            lines.append("|---------|-----|----------|--------|----|----------------|------------|------------|")
            for col in region.columns:
                pk = "tak" if col.primary_key else "—"
                link_parts: list[str] = []
                if col.link_target:
                    link_parts.append(f"→strona {col.link_target}")
                if col.link_text:
                    link_parts.append(col.link_text)
                if col.master_region or col.master_column:
                    link_parts.append(f"master: {col.master_region or '?'}.{col.master_column or '?'}")
                link = "; ".join(link_parts) or "—"
                sort = "tak" if col.sortable else "—"
                align = col.column_alignment or col.heading_alignment or "—"
                lines.append(
                    f"| {col.name}{_bo_suffix(col.build_option)} | {col.type} | {col.heading or '—'} "
                    f"| {col.source_column or '—'} | {pk} | {link} | {sort} | {align} |"
                )
            lines.append("")

        return lines

    def _render_shared_components(self, app: ApexApp) -> list[str]:
        """Renderuj sekcję Shared Components."""
        lines: list[str] = []
        lines.append("## Shared Components")
        lines.append("")

        # LOV-y
        if app.lovs:
            lines.append("### Listy wartości (LOV)")
            lines.append("")
            for lov in app.lovs:
                lines.append(f"**{lov.name}** — typ: {lov.source_type}")
                if lov.source_table:
                    lines.append(f"- Tabela: `{lov.source_table}`")
                if lov.return_column:
                    lines.append(f"- Return: `{lov.return_column}`")
                if lov.display_column:
                    lines.append(f"- Display: `{lov.display_column}`")
                if lov.sql_query and self._should_include_code():
                    lines.append(f"```sql")
                    lines.append(lov.sql_query)
                    lines.append(f"```")
                if lov.entries:
                    vals = ", ".join(f"{e['display']}→{e['return']}" for e in lov.entries)
                    lines.append(f"- Wartości: {vals}")
                lines.append("")

        # Schematy autentykacji (LDAP/ADFS/APEX)
        if app.authentications:
            lines.append("### Schematy autentykacji")
            lines.append("")
            for auth_s in app.authentications:
                lines.append(f"**{auth_s.name}** — typ: {auth_s.type or '?'}")
                if auth_s.host:
                    lines.append(f"- Host: `{auth_s.host}`:{auth_s.port or 389}")
                if auth_s.use_ssl:
                    lines.append(f"- SSL: {auth_s.use_ssl}")
                if auth_s.dn_string:
                    lines.append(f"- DN string: `{auth_s.dn_string}`")
                lines.append("")

        # Autoryzacje
        if app.authorizations:
            lines.append("### Schematy autoryzacji")
            lines.append("")
            for auth in app.authorizations:
                lines.append(f"**{auth.name}** — typ: {auth.type or '?'}")
                if auth.role_or_group:
                    lines.append(f"- Rola: {auth.role_or_group}")
                if auth.code and self._should_include_code():
                    lines.append(f"```plsql")
                    lines.append(auth.code)
                    lines.append(f"```")
                lines.append("")

        # Plugini
        if app.plugins:
            lines.append("### Pluginy")
            lines.append("")
            for p in app.plugins:
                avail = f" [{', '.join(p.available_as)}]" if p.available_as else ""
                lines.append(f"- **{p.name}** ({p.plugin_type or '?'}{avail})")
            lines.append("")

        # Search Configurations
        if app.search_configs:
            lines.append("### Wyszukiwanie (Search Configurations)")
            lines.append("")
            for s in app.search_configs:
                lines.append(f"**{s.name}** — typ: {s.search_type or '?'}")
                if s.sql_query and self._should_include_code():
                    lines.append(f"```sql")
                    lines.append(s.sql_query)
                    lines.append(f"```")
                lines.append("")

        # Data Load Definitions
        if app.data_load_defs:
            lines.append("### Definicje ładowania danych")
            lines.append("")
            for d in app.data_load_defs:
                lines.append(f"- **{d.name}** → tabela `{d.table_name or '?'}` (metoda: {d.loading_method or '?'})")
            lines.append("")

        # Pliki statyczne
        if app.static_files:
            lines.append("### Pliki statyczne aplikacji")
            lines.append("")
            for sf in app.static_files:
                lines.append(f"- `{sf.file_name}` ({sf.mime_type or '?'})")
            lines.append("")

        # Grupy stron
        if app.page_groups:
            lines.append("### Grupy stron")
            lines.append("")
            for g in app.page_groups:
                lines.append(f"- {g.name}")
            lines.append("")

        # Nawigacja
        if app.nav_lists:
            lines.append("### Listy nawigacyjne")
            lines.append("")
            for nav in app.nav_lists:
                lines.append(f"**{nav.name}**")
                # Indentacja wpisów na podstawie parent-entry
                labels = {e.get("label") for e in nav.entries if e.get("label")}
                for entry in nav.entries:
                    label = entry.get("label", "?")
                    target = entry.get("target_page", "?")
                    parent = entry.get("parent")
                    indent = "  " if parent and parent in labels else ""
                    parent_info = f" (pod: {parent})" if parent and parent not in labels else ""
                    lines.append(f"{indent}- {label} → strona {target}{parent_info}")
                lines.append("")

        # App Items
        if app.app_items:
            lines.append("### Zmienne globalne")
            lines.append("")
            lines.append("| Nazwa | Zakres |")
            lines.append("|-------|--------|")
            for item in app.app_items:
                lines.append(f"| {item.name} | {item.scope or '?'} |")
            lines.append("")

        # Build Options
        if app.build_options:
            lines.append("### Opcje budowania")
            lines.append("")
            for bo in app.build_options:
                lines.append(f"- **{bo.name}** — {bo.status}")
            lines.append("")

        # Breadcrumbs
        if app.breadcrumbs:
            lines.append("### Breadcrumbs")
            lines.append("")
            for bc in app.breadcrumbs:
                entries_str = " → ".join(
                    f"{e.get('name', '?')} (strona {e.get('page_number', '?')})"
                    for e in bc.entries
                )
                lines.append(f"- **{bc.name}:** {entries_str}")
            lines.append("")

        # ACL Roles
        if app.acl_roles:
            lines.append("### Role ACL")
            lines.append("")
            for role in app.acl_roles:
                lines.append(f"- **{role.name}** (static_id: {role.static_id or '?'})")
            lines.append("")

        return lines

    def _render_ddl(self, ddl: DDLSchema) -> list[str]:
        """Renderuj sekcję DDL — struktura bazy danych."""
        lines: list[str] = []
        lines.append("## Struktura bazy danych (DDL)")
        lines.append("")

        # Tabele
        if ddl.tables:
            lines.append("### Tabele")
            lines.append("")
            for table in ddl.tables:
                lines.append(f"#### Tabela: `{table.name}`")
                if table.comment:
                    lines.append(f"> {table.comment}")
                lines.append("")

                if table.columns:
                    lines.append("| Kolumna | Typ | NULL | Domyślna | PK |")
                    lines.append("|---------|-----|------|----------|----|")
                    for col in table.columns:
                        null_str = "tak" if col.nullable else "nie"
                        pk_str = "tak" if col.primary_key else "—"
                        default_str = col.default or "—"
                        lines.append(
                            f"| `{col.name}` | {col.data_type} "
                            f"| {null_str} | {default_str} | {pk_str} |"
                        )
                    lines.append("")

                # Komentarze kolumn
                if table.column_comments:
                    lines.append("**Komentarze kolumn:**")
                    for cname, comment in table.column_comments.items():
                        lines.append(f"- `{cname}`: {comment}")
                    lines.append("")

                # Ograniczenia (FK, CHECK, UNIQUE)
                fk_constraints = [c for c in table.constraints if c.type == "FOREIGN KEY"]
                other_constraints = [c for c in table.constraints
                                     if c.type not in ("PRIMARY KEY", "FOREIGN KEY")]
                if fk_constraints:
                    lines.append("**Klucze obce:**")
                    for fk in fk_constraints:
                        cols = ", ".join(fk.columns)
                        lines.append(
                            f"- `{cols}` → `{fk.ref_table}`.`{fk.ref_column}`"
                        )
                    lines.append("")
                if other_constraints:
                    lines.append("**Ograniczenia:**")
                    for c in other_constraints:
                        if c.check_condition:
                            lines.append(f"- {c.name} ({c.type}): `{c.check_condition}`")
                        else:
                            cols = ", ".join(c.columns)
                            lines.append(f"- {c.name} ({c.type}): `{cols}`")
                    lines.append("")

        # Widoki
        if ddl.views:
            lines.append("### Widoki")
            lines.append("")
            for view in ddl.views:
                lines.append(f"#### Widok: `{view.name}`")
                if view.comment:
                    lines.append(f"> {view.comment}")
                    lines.append("")
                if view.sql and self._should_include_code():
                    lines.append("```sql")
                    lines.append(view.sql)
                    lines.append("```")
                    lines.append("")

        # Pakiety
        if ddl.packages:
            lines.append("### Pakiety PL/SQL")
            lines.append("")
            for pkg in ddl.packages:
                lines.append(f"#### Pakiet: `{pkg.name}`")
                lines.append("")
                if pkg.code and self._should_include_code():
                    lines.append("```plsql")
                    lines.append(pkg.code)
                    lines.append("```")
                    lines.append("")

        # Procedury/Funkcje
        if ddl.procedures:
            lines.append("### Procedury i funkcje")
            lines.append("")
            for proc in ddl.procedures:
                lines.append(f"#### `{proc.name}`")
                lines.append("")
                if proc.code and self._should_include_code():
                    lines.append("```plsql")
                    lines.append(proc.code)
                    lines.append("```")
                    lines.append("")

        # Sekwencje
        if ddl.sequences:
            lines.append("### Sekwencje")
            lines.append("")
            for seq in ddl.sequences:
                parts = [f"`{seq.name}`"]
                if seq.start_with:
                    parts.append(f"start: {seq.start_with}")
                if seq.increment_by:
                    parts.append(f"increment: {seq.increment_by}")
                lines.append(f"- {', '.join(parts)}")
            lines.append("")

        return lines
