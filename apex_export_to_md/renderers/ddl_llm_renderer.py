"""DDL LLM Renderer — generuje skondensowany format liniowy DDL.

Osobny plik wyjściowy ze strukturą bazy danych zoptymalizowany dla LLM.
"""
from __future__ import annotations
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp


class DDLLLMRenderer(BaseRenderer):
    """Renderer DDL zoptymalizowany dla LLM — format liniowy."""

    def render(self, app: ApexApp) -> str:
        """Generuj skondensowany tekst DDL."""
        if not app.ddl_schema:
            return ""
        ddl = app.ddl_schema
        lines: list[str] = []

        lines.append(f"DDL_SCHEMA:{app.id}|{app.name}")

        for table in ddl.tables:
            parts = [f"===TBL:{table.name}"]
            if table.comment:
                parts.append(f"comment:{table.comment[:80]}")
            lines.append("|".join(parts))
            for col in table.columns:
                col_parts = [f"TBLCOL:{col.name}", col.data_type]
                if not col.nullable:
                    col_parts.append("nn:true")
                if col.primary_key:
                    col_parts.append("pk:true")
                if col.default:
                    col_parts.append(f"def:{col.default}")
                lines.append("|".join(col_parts))
                if col.name in table.column_comments:
                    lines.append(f"TBLCOL_COMMENT:{col.name}|{table.column_comments[col.name]}")
            for c in table.constraints:
                if c.type == "FOREIGN KEY":
                    cols = ",".join(c.columns)
                    lines.append(f"FK:{cols}->{c.ref_table}.{c.ref_column}")
                elif c.type == "CHECK" and c.check_condition:
                    lines.append(f"CHK:{c.name}|{c.check_condition}")

        for view in ddl.views:
            parts = [f"===VIEW:{view.name}"]
            if view.comment:
                parts.append(f"comment:{view.comment[:80]}")
            lines.append("|".join(parts))
            if view.sql and self._should_include_code():
                lines.append("```sql")
                lines.append(view.sql)
                lines.append("```")

        for pkg in ddl.packages:
            lines.append(f"===PKG:{pkg.name}")
            if pkg.code and self._should_include_code():
                lines.append("```plsql")
                lines.append(pkg.code)
                lines.append("```")

        for proc in ddl.procedures:
            lines.append(f"===DDL_PROC:{proc.name}")
            if proc.code and self._should_include_code():
                lines.append("```plsql")
                lines.append(proc.code)
                lines.append("```")

        for seq in ddl.sequences:
            parts = [f"===SEQ:{seq.name}"]
            if seq.start_with:
                parts.append(f"start:{seq.start_with}")
            if seq.increment_by:
                parts.append(f"incr:{seq.increment_by}")
            lines.append("|".join(parts))

        for idx in ddl.indexes:
            parts = [f"IDX:{idx.name}", f"tbl:{idx.table_name}", f"cols:{','.join(idx.columns)}"]
            if idx.unique:
                parts.append("unique:true")
            lines.append("|".join(parts))

        for trg in ddl.triggers:
            parts = [f"===TRG:{trg.name}"]
            if trg.table_name:
                parts.append(f"tbl:{trg.table_name}")
            lines.append("|".join(parts))
            if trg.code and self._should_include_code():
                lines.append("```plsql")
                lines.append(trg.code)
                lines.append("```")

        return "\n".join(lines)
