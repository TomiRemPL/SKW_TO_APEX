"""Human Renderer — generuje czytelny Markdown z modelu APEX.

Format wyjściowy: nagłówki, tabele, bloki kodu — czytelny dla człowieka.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, ApexPage, Region, Column, Process, DynamicAction,
    Button, Branch, PageItem, Validation, LOV, Authorization,
    NavList, AppItem, BuildOption, Breadcrumb, AclRole,
)


class HumanRenderer(BaseRenderer):
    """Renderer Markdown czytelny dla człowieka."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny dokument Markdown."""
        lines: list[str] = []

        # Nagłówek aplikacji
        lines.append(f"# Aplikacja {app.name} (ID: {app.id}, alias: {app.alias})")
        lines.append("")

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

    def _render_page(self, page: ApexPage) -> list[str]:
        """Renderuj pojedynczą stronę."""
        lines: list[str] = []
        lines.append(f"### Strona {page.id}: {page.name}")
        if page.title and page.title != page.name:
            lines.append(f"- **Tytuł:** {page.title}")
        lines.append(f"- **Tryb:** {page.page_mode}")
        if page.security:
            auth = page.security.get("authentication", "")
            if auth:
                lines.append(f"- **Uwierzytelnianie:** {auth}")
        lines.append("")

        # Regiony
        for region in page.regions:
            lines.extend(self._render_region(region))

        # Elementy formularza
        if page.items:
            lines.append("#### Elementy formularza")
            lines.append("")
            lines.append("| Nazwa | Typ | Etykieta | Kolumna | LOV |")
            lines.append("|-------|-----|----------|---------|-----|")
            for item in page.items:
                lines.append(
                    f"| {item.name} | {item.type} "
                    f"| {item.label or '—'} | {item.source_column or '—'} "
                    f"| {item.lov or '—'} |"
                )
            lines.append("")

        # Przyciski
        if page.buttons:
            lines.append("#### Przyciski")
            lines.append("")
            for btn in page.buttons:
                hot = " **(primary)**" if btn.is_hot else ""
                target = f" → strona {btn.target_page}" if btn.target_page else ""
                lines.append(f"- **{btn.name}** — {btn.label or '?'} [{btn.action or '?'}]{hot}{target}")
            lines.append("")

        # Procesy
        if page.processes:
            lines.append("#### Procesy")
            lines.append("")
            for proc in page.processes:
                btn_info = f", przycisk: {proc.when_button_pressed}" if proc.when_button_pressed else ""
                lang_info = f", język: {proc.language}" if proc.language else ""
                lines.append(f"**{proc.name}** ({proc.point}{lang_info}{btn_info})")
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
                lines.append(f"- **{da.name}** — zdarzenie: {da.event}{trigger_info}")
                for step in da.actions:
                    lines.append(f"  - Krok: {step.type}")
                    if step.affected_elements:
                        lines.append(f"    - Wpływa na: {step.affected_elements}")
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
                lines.append(f"- {branch.name or '?'} → {target}{cond}")
            lines.append("")

        # Walidacje
        if page.validations:
            lines.append("#### Walidacje")
            lines.append("")
            for val in page.validations:
                lines.append(f"- **{val.name}** — typ: {val.type}")
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

        if page.js_inline:
            lines.append("#### JavaScript strony")
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
        lines.append(f"#### Region: {region.name}{title_part}")

        # Typ i źródło
        type_info = region.type
        if region.editable:
            ops = ", ".join(region.allowed_operations) if region.allowed_operations else "?"
            type_info += f" (edytowalny: {ops})"

        lines.append(f"- **Typ:** {type_info}")
        if region.source_table:
            lines.append(f"- **Źródło:** tabela `{region.source_table}`")
        if region.source_sql:
            lines.append(f"- **Źródło SQL:**")
            if self._should_include_code():
                lines.append(f"```sql")
                lines.append(region.source_sql)
                lines.append(f"```")
        lines.append("")

        # Kolumny jako tabela
        if region.columns:
            lines.append("| Kolumna | Typ | Nagłówek | Źródło | PK | Link |")
            lines.append("|---------|-----|----------|--------|----|------|")
            for col in region.columns:
                pk = "tak" if col.primary_key else "—"
                link = f"→strona {col.link_target}" if col.link_target else "—"
                lines.append(
                    f"| {col.name} | {col.type} | {col.heading or '—'} "
                    f"| {col.source_column or '—'} | {pk} | {link} |"
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

        # Nawigacja
        if app.nav_lists:
            lines.append("### Listy nawigacyjne")
            lines.append("")
            for nav in app.nav_lists:
                lines.append(f"**{nav.name}**")
                for entry in nav.entries:
                    label = entry.get("label", "?")
                    target = entry.get("target_page", "?")
                    lines.append(f"- {label} → {target}")
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
