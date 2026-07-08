"""DDL Script Renderer — generuje wykonywalny skrypt SQL tworzący obiekty bazy danych.

Generuje skrypt gotowy do uruchomienia na nowym schemacie Oracle.
Kolejność: sekwencje → tabele (bez FK) → widoki → pakiety → procedury → ALTER TABLE ADD FK.
Usuwa referencje do schematu źródłowego (np. "DAW".).
"""
from __future__ import annotations
import re
from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import (
    ApexApp, DDLSchema, DDLTable, DDLSequence, DDLView, DDLPackage, DDLProcedure,
)


class DDLScriptRenderer(BaseRenderer):
    """Renderer generujący wykonywalny skrypt SQL (DDL)."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny skrypt DDL."""
        if not app.ddl_schema:
            return ""
        ddl = app.ddl_schema
        lines: list[str] = []

        lines.append("-- ============================================================")
        lines.append(f"-- Skrypt DDL wygenerowany z aplikacji {app.name} (ID: {app.id})")
        lines.append("-- Uruchom na użytkowniku zalogowanym do docelowego schematu.")
        lines.append("-- ============================================================")
        lines.append("")

        # 1. Sekwencje
        if ddl.sequences:
            lines.append("-- ============================================================")
            lines.append("-- SEKWENCJE")
            lines.append("-- ============================================================")
            lines.append("")
            for seq in ddl.sequences:
                lines.append(self._render_sequence(seq, ddl.source_schema))
                lines.append("")

        # 2. Tabele (bez FK)
        if ddl.tables:
            lines.append("-- ============================================================")
            lines.append("-- TABELE")
            lines.append("-- ============================================================")
            lines.append("")
            for table in ddl.tables:
                lines.append(self._render_table(table, ddl.source_schema))
                lines.append("")

        # 3. Komentarze do tabel i kolumn
        comments_sql = self._render_comments(ddl)
        if comments_sql:
            lines.append("-- ============================================================")
            lines.append("-- KOMENTARZE")
            lines.append("-- ============================================================")
            lines.append("")
            lines.append(comments_sql)
            lines.append("")

        # 4. Widoki
        if ddl.views:
            lines.append("-- ============================================================")
            lines.append("-- WIDOKI")
            lines.append("-- ============================================================")
            lines.append("")
            for view in ddl.views:
                lines.append(self._render_view(view, ddl.source_schema))
                lines.append("")

        # 5. Pakiety PL/SQL
        if ddl.packages:
            lines.append("-- ============================================================")
            lines.append("-- PAKIETY PL/SQL")
            lines.append("-- ============================================================")
            lines.append("")
            for pkg in ddl.packages:
                lines.append(self._render_package(pkg, ddl.source_schema))
                lines.append("")

        # 6. Procedury i funkcje
        if ddl.procedures:
            lines.append("-- ============================================================")
            lines.append("-- PROCEDURY I FUNKCJE")
            lines.append("-- ============================================================")
            lines.append("")
            for proc in ddl.procedures:
                lines.append(self._render_procedure(proc, ddl.source_schema))
                lines.append("")

        # 7. Klucze obce (ALTER TABLE ADD CONSTRAINT FK)
        fk_sql = self._render_foreign_keys(ddl)
        if fk_sql:
            lines.append("-- ============================================================")
            lines.append("-- KLUCZE OBCE (FOREIGN KEYS)")
            lines.append("-- ============================================================")
            lines.append("")
            lines.append(fk_sql)
            lines.append("")

        # Podsumowanie obiektów
        lines.append("-- ============================================================")
        lines.append("-- PODSUMOWANIE")
        lines.append("-- ============================================================")
        lines.append(f"-- Sekwencje:  {len(ddl.sequences)}")
        lines.append(f"-- Tabele:     {len(ddl.tables)}")
        lines.append(f"-- Widoki:     {len(ddl.views)}")
        lines.append(f"-- Pakiety:    {len(ddl.packages)}")
        lines.append(f"-- Procedury:  {len(ddl.procedures)}")
        lines.append(f"-- RAZEM:      {len(ddl.sequences) + len(ddl.tables) + len(ddl.views) + len(ddl.packages) + len(ddl.procedures)}")
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- KONIEC SKRYPTU DDL")
        lines.append("-- ============================================================")

        return "\n".join(lines)
    def _strip_empty_lines(self, sql: str) -> str:
        """Usuń puste linie z bloku kodu SQL.

        APEX SQL Workshop traktuje pustą linię jako koniec kodu,
        dlatego usuwamy linie składające się wyłącznie z whitespace.
        """
        lines = sql.split('\n')
        return '\n'.join(line for line in lines if line.strip())
    def _strip_schema(self, sql: str, schema: str) -> str:
        """Usuń referencje do schematu źródłowego z SQL."""
        if not schema:
            return sql
        # Usuń "SCHEMA". oraz "SCHEMA".
        result = re.sub(rf'"{re.escape(schema)}"\s*\.\s*', '', sql)
        # Usuń SCHEMA. (bez cudzysłowów)
        result = re.sub(rf'\b{re.escape(schema)}\s*\.\s*', '', result, flags=re.IGNORECASE)
        return result

    def _render_sequence(self, seq: DDLSequence, schema: str) -> str:
        """Generuj CREATE SEQUENCE."""
        if seq.raw_sql:
            sql = self._strip_schema(seq.raw_sql, schema)
            sql = self._strip_empty_lines(sql)
            if not sql.rstrip().endswith(';'):
                sql += ';'
            return sql

        parts = [f'CREATE SEQUENCE "{seq.name}"']
        if seq.min_value:
            parts.append(f"  MINVALUE {seq.min_value}")
        if seq.max_value:
            parts.append(f"  MAXVALUE {seq.max_value}")
        if seq.increment_by:
            parts.append(f"  INCREMENT BY {seq.increment_by}")
        if seq.start_with:
            parts.append(f"  START WITH {seq.start_with}")
        if seq.nocache:
            parts.append("  NOCACHE")
        elif seq.cache_size:
            parts.append(f"  CACHE {seq.cache_size}")
        if seq.noorder:
            parts.append("  NOORDER")
        if seq.nocycle:
            parts.append("  NOCYCLE")
        return "\n".join(parts) + ";"

    def _render_table(self, table: DDLTable, schema: str) -> str:
        """Generuj CREATE TABLE (bez FK)."""
        if table.raw_sql:
            sql = self._strip_schema(table.raw_sql, schema)
            sql = self._strip_empty_lines(sql)
            if not sql.rstrip().endswith(';'):
                sql += ';'
            return sql

        # Fallback: generuj z modelu
        col_defs: list[str] = []
        for col in table.columns:
            col_def = f'    "{col.name}" {col.data_type}'
            if col.identity and col.identity_def:
                col_def += f" {col.identity_def}"
            elif col.default:
                col_def += f" DEFAULT {col.default}"
            if not col.nullable:
                col_def += " NOT NULL"
            col_def += " ENABLE"
            col_defs.append(col_def)

        # PK constraint
        pk_constraints = [c for c in table.constraints if c.type == "PRIMARY KEY"]
        for pk in pk_constraints:
            cols = ", ".join(f'"{c}"' for c in pk.columns)
            name_part = f'CONSTRAINT "{pk.name}" ' if pk.name else ""
            col_defs.append(f"    {name_part}PRIMARY KEY ({cols}) ENABLE")

        # UNIQUE, CHECK constraints (nie FK)
        for c in table.constraints:
            if c.type == "UNIQUE":
                cols = ", ".join(f'"{col}"' for col in c.columns)
                name_part = f'CONSTRAINT "{c.name}" ' if c.name else ""
                col_defs.append(f"    {name_part}UNIQUE ({cols}) ENABLE")
            elif c.type == "CHECK" and c.check_condition:
                name_part = f'CONSTRAINT "{c.name}" ' if c.name else ""
                col_defs.append(f"    {name_part}CHECK ({c.check_condition}) ENABLE")

        body = ",\n".join(col_defs)
        return f'CREATE TABLE "{table.name}" (\n{body}\n);'

    def _render_comments(self, ddl: DDLSchema) -> str:
        """Generuj COMMENT ON TABLE/COLUMN."""
        lines: list[str] = []
        for table in ddl.tables:
            if table.comment:
                escaped = table.comment.replace("'", "''")
                lines.append(f"COMMENT ON TABLE \"{table.name}\" IS '{escaped}';")
            for col_name, comment in table.column_comments.items():
                escaped = comment.replace("'", "''")
                lines.append(f"COMMENT ON COLUMN \"{table.name}\".\"{col_name}\" IS '{escaped}';")
        for view in ddl.views:
            if view.comment:
                escaped = view.comment.replace("'", "''")
                lines.append(f"COMMENT ON TABLE \"{view.name}\" IS '{escaped}';")
        return "\n".join(lines)

    def _render_view(self, view: DDLView, schema: str) -> str:
        """Generuj CREATE OR REPLACE VIEW."""
        sql = self._strip_schema(view.sql, schema)
        sql = self._strip_empty_lines(sql)
        return f'CREATE OR REPLACE VIEW "{view.name}" AS\n{sql};'

    def _render_package(self, pkg: DDLPackage, schema: str) -> str:
        """Generuj CREATE OR REPLACE PACKAGE."""
        code = self._strip_schema(pkg.code, schema)
        code = self._strip_empty_lines(code)
        return f"CREATE OR REPLACE PACKAGE {pkg.name} AS\n{code}\nEND {pkg.name};\n/"

    def _render_procedure(self, proc: DDLProcedure, schema: str) -> str:
        """Generuj CREATE OR REPLACE PROCEDURE/FUNCTION."""
        code = self._strip_schema(proc.code, schema)
        code = self._strip_empty_lines(code)
        return f"CREATE OR REPLACE {code}\nEND {proc.name};\n/"

    def _render_foreign_keys(self, ddl: DDLSchema) -> str:
        """Generuj ALTER TABLE ADD CONSTRAINT FOREIGN KEY."""
        lines: list[str] = []
        for table in ddl.tables:
            for c in table.constraints:
                if c.type == "FOREIGN KEY" and c.ref_table:
                    cols = ", ".join(f'"{col}"' for col in c.columns)
                    lines.append(
                        f'ALTER TABLE "{table.name}" ADD CONSTRAINT "{c.name}" '
                        f'FOREIGN KEY ({cols}) REFERENCES "{c.ref_table}" ("{c.ref_column}") ENABLE;'
                    )
        return "\n".join(lines)
