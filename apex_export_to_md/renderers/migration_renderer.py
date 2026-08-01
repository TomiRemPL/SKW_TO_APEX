"""Migration Renderer — generuje pełny skrypt migracyjny SQL z danymi.

Skrypt zawiera:
1. CREATE obiektów (bez FK)
2. DISABLE constraints i triggers
3. INSERT danych
4. Reset sekwencji/identity
5. ENABLE constraints i triggers
6. COMMIT
"""
from __future__ import annotations
import logging
from datetime import date, datetime
from typing import Any

from apex_export_to_md.renderers.ddl_script_renderer import DDLScriptRenderer
from apex_export_to_md.models import ApexApp, DDLSchema
from apex_export_to_md.config import AppConfig
from apex_export_to_md.db_exporter import ExportedData, TableData

logger = logging.getLogger(__name__)


class MigrationRenderer(DDLScriptRenderer):
    """Renderer generujący pełny skrypt migracyjny (DDL + dane)."""

    def __init__(self, config: AppConfig, db_data: ExportedData, timestamp: str = ""):
        super().__init__(config, timestamp)
        self._db_data = db_data

    def render(self, app: ApexApp) -> str:
        """Generuj pełny skrypt migracyjny."""
        if not app.ddl_schema:
            return ""
        ddl = app.ddl_schema
        lines: list[str] = []

        # Timestamp generowania
        if self._timestamp:
            lines.append("/*")
            lines.append(f" * Generated: {self._timestamp}")
            lines.append(" */")
            lines.append("")

        lines.append("-- ============================================================")
        lines.append(f"-- SKRYPT MIGRACYJNY — {app.name} (ID: {app.id})")
        lines.append("-- Uruchom na użytkowniku zalogowanym do docelowego schematu.")
        lines.append("-- ============================================================")
        lines.append("SET DEFINE OFF;")
        lines.append("")

        # ---- SEKCJA 1: CREATE obiektów ----
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 1: TWORZENIE OBIEKTÓW")
        lines.append("-- ============================================================")
        lines.append("")
        lines.append(self._render_create_objects(ddl))

        # ---- SEKCJA 2: DISABLE constraints i triggers ----
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 2: WYŁĄCZENIE WIĘZÓW INTEGRALNOŚCI")
        lines.append("-- ============================================================")
        lines.append("")
        lines.append(self._render_disable_constraints(ddl))

        # ---- SEKCJA 3: INSERT danych ----
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 3: WGRANIE DANYCH")
        lines.append("-- ============================================================")
        lines.append("")
        lines.append(self._render_inserts())

        # ---- SEKCJA 4: Reset sekwencji/identity ----
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 4: USTAWIENIE SEKWENCJI I IDENTITY")
        lines.append("-- ============================================================")
        lines.append("")
        lines.append(self._render_reset_sequences(ddl))

        # ---- SEKCJA 5: ENABLE constraints ----
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 5: WŁĄCZENIE WIĘZÓW INTEGRALNOŚCI")
        lines.append("-- ============================================================")
        lines.append("")
        lines.append(self._render_enable_constraints(ddl))

        # ---- SEKCJA 6: COMMIT ----
        lines.append("")
        lines.append("COMMIT;")

        # ---- PODSUMOWANIE DANYCH ----
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- PODSUMOWANIE EKSPORTU")
        lines.append("-- ============================================================")
        total_rows = 0
        for table_data in self._db_data.tables:
            row_count = len(table_data.rows)
            total_rows += row_count
            lines.append(f"-- Tabela {table_data.table_name:40s}: {row_count} wierszy")
        lines.append(f"-- {'─' * 40}  {'─' * 10}")
        lines.append(f"-- {'RAZEM':40s}: {total_rows} wierszy")
        lines.append(f"-- Sekwencje: {len(self._db_data.sequences)}")
        lines.append(f"-- Kolumny identity: {len(self._db_data.identity_max_values)}")

        # ---- SEKCJA 7: WALIDACJA KOMPLETNOŚCI ----
        lines.append("")
        lines.append(self._render_validation_section(ddl))

        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- KONIEC SKRYPTU MIGRACYJNEGO")
        lines.append("-- ============================================================")

        cleaned_lines: list[str] = []
        for line in lines:
            if line.strip() == "" and (not cleaned_lines or cleaned_lines[-1] == ""):
                continue
            cleaned_lines.append(line if line.strip() else "")

        return "\n".join(cleaned_lines)

    def _render_create_objects(self, ddl: DDLSchema) -> str:
        """Generuj DDL tworzenia obiektów (sekwencje + tabele z FK, widoki, pakiety, procedury)."""
        lines: list[str] = []
        schema = ddl.source_schema

        # Sekwencje
        for seq in ddl.sequences:
            lines.append(self._render_sequence(seq, schema))
            lines.append("")

        # Tabele (z FK — wyłączymy je potem)
        for table in ddl.tables:
            lines.append(self._render_table(table, schema))
            lines.append("")

        # FK
        fk_sql = self._render_foreign_keys(ddl)
        if fk_sql:
            lines.append(fk_sql)
            lines.append("")

        # Indeksy
        for idx in ddl.indexes:
            lines.append(self._render_index(idx, schema))
            lines.append("")

        # Widoki
        for view in ddl.views:
            lines.append(self._render_view(view, schema))
            lines.append("")

        # Pakiety
        for pkg in ddl.packages:
            lines.append(self._render_package(pkg, schema))
            lines.append("")

        # Procedury
        for proc in ddl.procedures:
            lines.append(self._render_procedure(proc, schema))
            lines.append("")

        # Triggery
        for trg in ddl.triggers:
            lines.append(self._render_trigger(trg, schema))
            lines.append("")

        return "\n".join(lines)

    def _render_disable_constraints(self, ddl: DDLSchema) -> str:
        """Generuj ALTER TABLE DISABLE CONSTRAINT dla FK oraz DISABLE TRIGGER."""
        lines: list[str] = []
        for table in ddl.tables:
            for c in table.constraints:
                if c.type == "FOREIGN KEY" and c.name:
                    lines.append(
                        f'ALTER TABLE "{table.name}" DISABLE CONSTRAINT "{c.name}";'
                    )
        for trg in ddl.triggers:
            lines.append(f'ALTER TRIGGER "{trg.name}" DISABLE;')
        return "\n".join(lines)

    def _render_enable_constraints(self, ddl: DDLSchema) -> str:
        """Generuj ALTER TABLE ENABLE CONSTRAINT dla FK oraz ENABLE TRIGGER."""
        lines: list[str] = []
        for table in ddl.tables:
            for c in table.constraints:
                if c.type == "FOREIGN KEY" and c.name:
                    lines.append(
                        f'ALTER TABLE "{table.name}" ENABLE CONSTRAINT "{c.name}";'
                    )
        for trg in ddl.triggers:
            lines.append(f'ALTER TRIGGER "{trg.name}" ENABLE;')
        return "\n".join(lines)

    def _render_inserts(self) -> str:
        """Generuj INSERT INTO ... VALUES dla wszystkich tabel."""
        lines: list[str] = []
        for table_data in self._db_data.tables:
            if not table_data.rows:
                lines.append(f"-- Tabela {table_data.table_name}: brak danych")
                lines.append("")
                continue
            lines.append(f"-- Tabela: {table_data.table_name} ({len(table_data.rows)} wierszy)")
            cols_str = ", ".join(f'"{c}"' for c in table_data.columns)
            for i, row in enumerate(table_data.rows):
                values = ", ".join(self._format_value(v) for v in row)
                lines.append(
                    f'INSERT INTO "{table_data.table_name}" ({cols_str}) VALUES ({values});'
                )
                # COMMIT co 1000 wierszy
                if (i + 1) % 1000 == 0:
                    lines.append("COMMIT;")
            lines.append("COMMIT;")
            lines.append("")
        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Formatuj wartość Pythona na literał SQL Oracle."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, datetime):
            return f"TO_TIMESTAMP('{value.strftime('%Y-%m-%d %H:%M:%S.%f')}', 'YYYY-MM-DD HH24:MI:SS.FF')"
        if isinstance(value, date):
            return f"TO_DATE('{value.strftime('%Y-%m-%d')}', 'YYYY-MM-DD')"
        if isinstance(value, bytes):
            hex_str = value.hex()
            return f"HEXTORAW('{hex_str}')"
        # String — escape apostrofów
        escaped = str(value).replace("'", "''")
        # Dla CLOB/długich stringów użyj q-quoting jeśli zawiera apostrofy
        if len(escaped) > 4000:
            return f"TO_CLOB('{escaped[:4000]}') || TO_CLOB('{escaped[4000:]}')"
        return f"'{escaped}'"

    def _render_reset_sequences(self, ddl: DDLSchema) -> str:
        """Generuj ALTER SEQUENCE ... RESTART WITH i reset identity."""
        lines: list[str] = []

        # Sekwencje
        for seq_val in self._db_data.sequences:
            if seq_val.current_value > 0:
                lines.append(
                    f'ALTER SEQUENCE "{seq_val.name}" RESTART START WITH {seq_val.current_value};'
                )

        # Kolumny identity
        for key, max_val in self._db_data.identity_max_values.items():
            table_name, col_name = key.split(".", 1)
            next_val = max_val + 1
            lines.append(
                f'ALTER TABLE "{table_name}" MODIFY "{col_name}" '
                f'GENERATED BY DEFAULT ON NULL AS IDENTITY (START WITH {next_val});'
            )

        return "\n".join(lines)

    def _render_validation_section(self, ddl: DDLSchema) -> str:
        """Generuj sekcję walidacji kompletności skryptu migracyjnego.

        Blok PL/SQL sprawdzający:
        - Istnienie wszystkich tabel, sekwencji, widoków, pakietów
        - Zgodność COUNT(*) każdej tabeli z oczekiwaną liczbą wierszy
        """
        lines: list[str] = []
        lines.append("-- ============================================================")
        lines.append("-- SEKCJA 7: WALIDACJA KOMPLETNOŚCI MIGRACJI")
        lines.append("-- ============================================================")
        lines.append("-- Uruchom po wykonaniu skryptu, aby zweryfikować poprawność.")
        lines.append("-- Wymaga: SET SERVEROUTPUT ON")
        lines.append("")
        lines.append("SET SERVEROUTPUT ON;")
        lines.append("DECLARE")
        lines.append("  v_count     NUMBER;")
        lines.append("  v_expected  NUMBER;")
        lines.append("  v_errors    NUMBER := 0;")
        lines.append("  v_checks    NUMBER := 0;")
        lines.append("  v_exists    NUMBER;")
        lines.append("BEGIN")
        lines.append("  DBMS_OUTPUT.PUT_LINE('=== WALIDACJA MIGRACJI ===');")
        lines.append("  DBMS_OUTPUT.PUT_LINE('');")

        # Sprawdź tabele
        lines.append("  -- Sprawdzenie tabel")
        for table in ddl.tables:
            lines.append(f"  SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = '{table.name}';")
            lines.append(f"  v_checks := v_checks + 1;")
            lines.append(f"  IF v_exists = 0 THEN")
            lines.append(f"    DBMS_OUTPUT.PUT_LINE('[FAIL] Tabela {table.name} - NIE ISTNIEJE');")
            lines.append(f"    v_errors := v_errors + 1;")
            lines.append(f"  ELSE")
            lines.append(f"    DBMS_OUTPUT.PUT_LINE('[OK]   Tabela {table.name}');")
            lines.append(f"  END IF;")

        # Sprawdź sekwencje
        if ddl.sequences:
            lines.append("  -- Sprawdzenie sekwencji")
            for seq in ddl.sequences:
                lines.append(f"  SELECT COUNT(*) INTO v_exists FROM USER_SEQUENCES WHERE SEQUENCE_NAME = '{seq.name}';")
                lines.append(f"  v_checks := v_checks + 1;")
                lines.append(f"  IF v_exists = 0 THEN")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[FAIL] Sekwencja {seq.name} - NIE ISTNIEJE');")
                lines.append(f"    v_errors := v_errors + 1;")
                lines.append(f"  ELSE")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[OK]   Sekwencja {seq.name}');")
                lines.append(f"  END IF;")

        # Sprawdź widoki
        if ddl.views:
            lines.append("  -- Sprawdzenie widoków")
            for view in ddl.views:
                lines.append(f"  SELECT COUNT(*) INTO v_exists FROM USER_VIEWS WHERE VIEW_NAME = '{view.name}';")
                lines.append(f"  v_checks := v_checks + 1;")
                lines.append(f"  IF v_exists = 0 THEN")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[FAIL] Widok {view.name} - NIE ISTNIEJE');")
                lines.append(f"    v_errors := v_errors + 1;")
                lines.append(f"  ELSE")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[OK]   Widok {view.name}');")
                lines.append(f"  END IF;")

        # Sprawdź pakiety
        if ddl.packages:
            lines.append("  -- Sprawdzenie pakietów")
            for pkg in ddl.packages:
                lines.append(f"  SELECT COUNT(*) INTO v_exists FROM USER_OBJECTS WHERE OBJECT_NAME = '{pkg.name}' AND OBJECT_TYPE = 'PACKAGE';")
                lines.append(f"  v_checks := v_checks + 1;")
                lines.append(f"  IF v_exists = 0 THEN")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[FAIL] Pakiet {pkg.name} - NIE ISTNIEJE');")
                lines.append(f"    v_errors := v_errors + 1;")
                lines.append(f"  ELSE")
                lines.append(f"    DBMS_OUTPUT.PUT_LINE('[OK]   Pakiet {pkg.name}');")
                lines.append(f"  END IF;")

        # Sprawdź liczność danych w tabelach
        lines.append("  DBMS_OUTPUT.PUT_LINE('');")
        lines.append("  DBMS_OUTPUT.PUT_LINE('--- Weryfikacja liczby wierszy ---');")
        for table_data in self._db_data.tables:
            expected = len(table_data.rows)
            lines.append(f"  BEGIN")
            lines.append(f"    v_expected := {expected};")
            lines.append(f"    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM \"{table_data.table_name}\"' INTO v_count;")
            lines.append(f"    v_checks := v_checks + 1;")
            lines.append(f"    IF v_count = v_expected THEN")
            lines.append(f"      DBMS_OUTPUT.PUT_LINE('[OK]   {table_data.table_name}: ' || v_count || ' wierszy');")
            lines.append(f"    ELSE")
            lines.append(f"      DBMS_OUTPUT.PUT_LINE('[FAIL] {table_data.table_name}: ' || v_count || ' (oczekiwano: ' || v_expected || ')');")
            lines.append(f"      v_errors := v_errors + 1;")
            lines.append(f"    END IF;")
            lines.append(f"  EXCEPTION WHEN OTHERS THEN")
            lines.append(f"    DBMS_OUTPUT.PUT_LINE('[FAIL] {table_data.table_name}: blad odczytu - ' || SQLERRM);")
            lines.append(f"    v_errors := v_errors + 1;")
            lines.append(f"  END;")

        # Podsumowanie
        lines.append("  DBMS_OUTPUT.PUT_LINE('');")
        lines.append("  DBMS_OUTPUT.PUT_LINE('=== WYNIK WALIDACJI ===');")
        lines.append("  DBMS_OUTPUT.PUT_LINE('Sprawdzono: ' || v_checks || ' elementow');")
        lines.append("  IF v_errors = 0 THEN")
        lines.append("    DBMS_OUTPUT.PUT_LINE('Status: PASS - wszystkie obiekty i dane poprawne');")
        lines.append("  ELSE")
        lines.append("    DBMS_OUTPUT.PUT_LINE('Status: FAIL - ' || v_errors || ' bledow');")
        lines.append("  END IF;")
        lines.append("END;")
        lines.append("/")

        return "\n".join(lines)
