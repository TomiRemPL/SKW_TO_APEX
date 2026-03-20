# apex_export_to_md/renderers/db_llm_renderer.py
"""LLM Renderer DB — generuje skondensowany format liniowy dla bazy danych.

Prefiksy: TBL, COL, FK, UQ, CHK, IDX, VW, VCOL, PKG, PROC, FUNC, CONST, SEQ.
"""
from __future__ import annotations
from apex_export_to_md.renderers.db_base_renderer import DbBaseRenderer
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbView, DbSequence, DbPackage, DbSubprogram,
)


class DbLLMRenderer(DbBaseRenderer):
    """Renderer LLM — format kondensowany dla bazy danych."""

    def render(self, schema: DbSchema) -> str:
        """Generuj skondensowany format liniowy z modelu bazy danych."""
        lines: list[str] = []
        lines.append("SCHEMA:DB")

        for table in schema.tables:
            lines.extend(self._render_table(table))

        for view in schema.views:
            lines.extend(self._render_view(view))

        for pkg in schema.packages:
            lines.extend(self._render_package(pkg))

        for seq in schema.sequences:
            parts = [f"SEQ:{seq.name}"]
            if seq.start_with:
                parts.append(f"START:{seq.start_with}")
            if seq.increment_by:
                parts.append(f"INCR:{seq.increment_by}")
            lines.append("|".join(parts))

        return "\n".join(lines)

    def _render_table(self, table: DbTable) -> list[str]:
        """Renderuj tabelę z kolumnami i constraint'ami."""
        lines: list[str] = []
        comment = table.comment or ""
        lines.append(f"TBL:{table.name}|{comment}")

        # Zbierz kolumny klucza głównego
        pk_cols: set[str] = set()
        for c in table.constraints:
            if c.constraint_type == "PK":
                pk_cols.update(c.columns)

        # Renderuj kolumny
        for col in table.columns:
            parts = [f"  COL:{col.name}", col.data_type]
            parts.append("NN" if not col.nullable else "NULL")
            parts.append(col.default or "")
            if col.name in pk_cols:
                parts.append("PK")
            if col.identity:
                parts.append("IDENTITY")
            if col.comment:
                parts.append(col.comment)
            lines.append("|".join(parts))

        # Renderuj constraint'y (FK, UQ, CHK)
        for c in table.constraints:
            if c.constraint_type == "FK":
                cols = ",".join(c.columns)
                ref_cols = ",".join(c.ref_columns) if c.ref_columns else ""
                lines.append(f"  FK:{c.name}|{cols}→{c.ref_table}.{ref_cols}")
            elif c.constraint_type == "UQ":
                cols = ",".join(c.columns)
                lines.append(f"  UQ:{cols}")
            elif c.constraint_type == "CHK":
                lines.append(f"  CHK:{c.check_expression or ''}")

        # Renderuj indeksy
        for idx in table.indexes:
            cols = ",".join(idx.columns)
            uq = "UNIQUE" if idx.unique else ""
            lines.append(f"  IDX:{idx.name}|{cols}|{uq}")

        return lines

    def _render_view(self, view: DbView) -> list[str]:
        """Renderuj widok z kolumnami i pierwszą linią SQL."""
        lines: list[str] = []
        comment = view.comment or ""
        lines.append(f"VW:{view.name}|{comment}")
        for col in view.columns:
            lines.append(f"  VCOL:{col}")
        if view.sql:
            first_line = view.sql.strip().split("\n")[0]
            lines.append(f"  SQL:{first_line}")
        return lines

    def _render_package(self, pkg: DbPackage) -> list[str]:
        """Renderuj pakiet PL/SQL z podprogramami specyfikacji i ciała."""
        lines: list[str] = []
        lines.append(f"PKG:{pkg.name}")

        if pkg.spec_subprograms:
            lines.append("  SPEC:")
            for sub in pkg.spec_subprograms:
                lines.append(self._render_subprogram(sub, indent="  "))

        if pkg.body_subprograms:
            lines.append("  BODY:")
            for sub in pkg.body_subprograms:
                lines.append(self._render_subprogram(sub, indent="  "))

        for const in pkg.constants:
            lines.append(f"  CONST:{const}")

        if pkg.body_source:
            line_count = len(pkg.body_source.strip().split("\n"))
            lines.append(f"  CODE:{line_count} lines")

        return lines

    def _render_subprogram(self, sub: DbSubprogram, indent: str = "") -> str:
        """Renderuj jeden podprogram (procedurę lub funkcję) w formacie jednoliniowym."""
        params = ",".join(
            f"{p.name} {p.direction} {p.data_type}" for p in sub.parameters
        )
        prefix = "FUNC" if sub.subprogram_type == "FUNCTION" else "PROC"
        parts = [f"{indent}{prefix}:{sub.name}({params})"]
        if sub.return_type:
            parts[0] += f"→{sub.return_type}"
        if sub.description:
            parts.append(sub.description)
        if sub.visibility == "private":
            parts.append("private")
        return "|".join(parts)
