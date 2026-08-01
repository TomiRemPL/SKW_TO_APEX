"""DDL Human Renderer — generuje czytelny Markdown z modelu DDL.

Osobny plik wyjściowy opisujący strukturę bazy danych.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, DDLSchema,
)


class DDLHumanRenderer(BaseRenderer):
    """Renderer Markdown DDL czytelny dla człowieka."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny dokument Markdown ze strukturą bazy danych."""
        if not app.ddl_schema:
            return ""
        ddl = app.ddl_schema
        lines: list[str] = []

        # Timestamp generowania
        if self._timestamp:
            lines.append(f"<!-- Generated: {self._timestamp} -->")
            lines.append("")

        lines.append(f"# Struktura bazy danych — {app.name} (ID: {app.id})")
        lines.append("")

        # Tabele
        if ddl.tables:
            lines.append("## Tabele")
            lines.append("")
            for table in ddl.tables:
                lines.append(f"### Tabela: `{table.name}`")
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
                        name_part = f"{fk.name}: " if fk.name else ""
                        lines.append(
                            f"- {name_part}`{cols}` → `{fk.ref_table}`.`{fk.ref_column}`"
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
            lines.append("## Widoki")
            lines.append("")
            for view in ddl.views:
                lines.append(f"### Widok: `{view.name}`")
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
            lines.append("## Pakiety PL/SQL")
            lines.append("")
            for pkg in ddl.packages:
                lines.append(f"### Pakiet: `{pkg.name}`")
                lines.append("")
                if pkg.code and self._should_include_code():
                    lines.append("```plsql")
                    lines.append(pkg.code)
                    lines.append("```")
                    lines.append("")

        # Procedury/Funkcje
        if ddl.procedures:
            lines.append("## Procedury i funkcje")
            lines.append("")
            for proc in ddl.procedures:
                lines.append(f"### `{proc.name}`")
                lines.append("")
                if proc.code and self._should_include_code():
                    lines.append("```plsql")
                    lines.append(proc.code)
                    lines.append("```")
                    lines.append("")

        # Sekwencje
        if ddl.sequences:
            lines.append("## Sekwencje")
            lines.append("")
            for seq in ddl.sequences:
                parts = [f"`{seq.name}`"]
                if seq.start_with:
                    parts.append(f"start: {seq.start_with}")
                if seq.increment_by:
                    parts.append(f"increment: {seq.increment_by}")
                lines.append(f"- {', '.join(parts)}")
            lines.append("")

        # Indeksy
        if ddl.indexes:
            lines.append("## Indeksy")
            lines.append("")
            for idx in ddl.indexes:
                unique_str = "UNIQUE " if idx.unique else ""
                cols = ", ".join(idx.columns)
                lines.append(f"- {unique_str}`{idx.name}` na `{idx.table_name}` ({cols})")
            lines.append("")

        # Triggery
        if ddl.triggers:
            lines.append("## Triggery")
            lines.append("")
            for trg in ddl.triggers:
                lines.append(f"### Trigger: `{trg.name}`")
                if trg.table_name:
                    lines.append(f"> Tabela: `{trg.table_name}`")
                lines.append("")
                if trg.code and self._should_include_code():
                    lines.append("```plsql")
                    lines.append(trg.code)
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)
