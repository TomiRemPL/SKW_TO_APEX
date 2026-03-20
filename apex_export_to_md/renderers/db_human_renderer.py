# apex_export_to_md/renderers/db_human_renderer.py
"""Human Renderer DB — generuje czytelny Markdown z dokumentacją bazy danych.

Zawiera: diagram Mermaid ER, tabele z kolumnami, widoki, pakiety PL/SQL, sekwencje.
"""
from __future__ import annotations
from apex_export_to_md.renderers.db_base_renderer import DbBaseRenderer
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbIndex,
    DbView, DbSequence, DbSubprogram, DbPackage,
)


class DbHumanRenderer(DbBaseRenderer):
    """Renderer Markdown czytelny dla człowieka — baza danych."""

    def render(self, schema: DbSchema) -> str:
        lines: list[str] = []
        lines.append("# Baza danych")
        lines.append("")

        er = self._render_mermaid_er(schema)
        if er:
            lines.append("## Diagram relacji")
            lines.append("")
            lines.extend(er)
            lines.append("")

        if schema.tables:
            lines.append("## Tabele")
            lines.append("")
            for table in schema.tables:
                lines.extend(self._render_table(table))

        if schema.views:
            lines.append("## Widoki")
            lines.append("")
            for view in schema.views:
                lines.extend(self._render_view(view))

        if schema.packages:
            lines.append("## Pakiety PL/SQL")
            lines.append("")
            for pkg in schema.packages:
                lines.extend(self._render_package(pkg))

        if schema.sequences:
            lines.append("## Sekwencje")
            lines.append("")
            lines.append("| Nazwa | Start | Increment | Min | Max |")
            lines.append("|-------|-------|-----------|-----|-----|")
            for seq in schema.sequences:
                lines.append(
                    f"| {seq.name} | {seq.start_with or '—'} "
                    f"| {seq.increment_by or '—'} "
                    f"| {seq.min_value or '—'} "
                    f"| {seq.max_value or '—'} |"
                )
            lines.append("")

        return "\n".join(lines)

    def _render_mermaid_er(self, schema: DbSchema) -> list[str]:
        """Generuj diagram Mermaid ER z FK constraints."""
        lines: list[str] = ["```mermaid", "erDiagram"]

        relations: list[tuple[str, str, str]] = []
        for table in schema.tables:
            for c in table.constraints:
                if c.constraint_type == "FK" and c.ref_table:
                    relations.append((c.ref_table, table.name, c.name))

        for parent, child, fk_name in relations:
            lines.append(f'    {parent} ||--o{{ {child} : "{fk_name}"')

        for table in schema.tables:
            lines.append(f"    {table.name} {{")
            shown = 0
            for col in table.columns:
                if shown >= 5:
                    break
                is_pk = any(
                    c.constraint_type == "PK" and col.name in c.columns
                    for c in table.constraints
                )
                is_fk = any(
                    c.constraint_type == "FK" and col.name in c.columns
                    for c in table.constraints
                )
                marker = " PK" if is_pk else (" FK" if is_fk else "")
                if is_pk or is_fk or shown < 3:
                    dt = col.data_type.split("(")[0]
                    lines.append(f"        {dt} {col.name}{marker}")
                    shown += 1
            lines.append("    }")

        lines.append("```")
        return lines

    def _render_table(self, table: DbTable) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Tabela: {table.name}")
        if table.comment:
            lines.append(f"> {table.comment}")
        lines.append("")

        if table.columns:
            lines.append("| Kolumna | Typ | NULL | Default | Komentarz |")
            lines.append("|---------|-----|------|---------|-----------|")
            for col in table.columns:
                null = "NOT NULL" if not col.nullable else "NULL"
                default = col.default or "—"
                comment = col.comment or "—"
                identity = " (IDENTITY)" if col.identity else ""
                lines.append(
                    f"| {col.name} | {col.data_type}{identity} "
                    f"| {null} | {default} | {comment} |"
                )
            lines.append("")

        pks = [c for c in table.constraints if c.constraint_type == "PK"]
        if pks:
            pk = pks[0]
            cols = ", ".join(pk.columns)
            lines.append(f"**Klucz główny:** {pk.name} ({cols})")
            lines.append("")

        fks = [c for c in table.constraints if c.constraint_type == "FK"]
        if fks:
            lines.append("**Foreign keys:**")
            for fk in fks:
                cols = ", ".join(fk.columns)
                ref_cols = ", ".join(fk.ref_columns) if fk.ref_columns else "?"
                lines.append(f"- {fk.name}: {cols} → {fk.ref_table}({ref_cols})")
            lines.append("")

        uqs = [c for c in table.constraints if c.constraint_type == "UQ"]
        if uqs:
            lines.append("**Unique constraints:**")
            for uq in uqs:
                cols = ", ".join(uq.columns)
                lines.append(f"- {uq.name}: ({cols})")
            lines.append("")

        chks = [c for c in table.constraints if c.constraint_type == "CHK"]
        if chks:
            lines.append("**Check constraints:**")
            for chk in chks:
                lines.append(f"- {chk.name}: `{chk.check_expression}`")
            lines.append("")

        if table.indexes:
            lines.append("**Indeksy:**")
            for idx in table.indexes:
                cols = ", ".join(idx.columns)
                uq = " (UNIQUE)" if idx.unique else ""
                lines.append(f"- {idx.name}: ({cols}){uq}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _render_view(self, view: DbView) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Widok: {view.name}")
        if view.comment:
            lines.append(f"> {view.comment}")
        if view.columns:
            lines.append(f"**Kolumny:** {', '.join(view.columns)}")
        lines.append("")
        if view.sql and self._should_include_code():
            lines.append("```sql")
            lines.append(view.sql)
            lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _render_package(self, pkg: DbPackage) -> list[str]:
        lines: list[str] = []
        lines.append(f"### Pakiet: {pkg.name}")
        lines.append("")

        if pkg.constants:
            lines.append("**Stałe:**")
            for const in pkg.constants:
                lines.append(f"- `{const}`")
            lines.append("")

        if pkg.spec_subprograms:
            lines.append("#### Specyfikacja")
            lines.append("")
            lines.append("| Procedura/Funkcja | Parametry | Zwraca | Opis |")
            lines.append("|-------------------|-----------|--------|------|")
            for sub in pkg.spec_subprograms:
                params = ", ".join(
                    f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
                ) or "—"
                ret = sub.return_type or "—"
                desc = sub.description or "—"
                lines.append(f"| {sub.name} | {params} | {ret} | {desc} |")
            lines.append("")

        private_subs = [s for s in pkg.body_subprograms if s.visibility == "private"]
        if private_subs:
            lines.append("#### Procedury prywatne (body)")
            lines.append("")
            for sub in private_subs:
                params = ", ".join(
                    f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
                ) or "—"
                desc = sub.description or ""
                lines.append(f"- **{sub.name}**({params}) — {desc}")
            lines.append("")

        if pkg.body_source and self._should_include_code():
            lines.append("#### Implementacja (body)")
            lines.append("")
            lines.append("```plsql")
            lines.append(pkg.body_source)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines
