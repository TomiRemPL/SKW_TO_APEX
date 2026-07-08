"""Rollback Renderer — generuje skrypt wycofujący migrację.

Skrypt zawiera instrukcje DROP w odwrotnej kolejności do tworzenia:
1. DROP pakietów i procedur
2. DROP widoków
3. DROP tabel (po wcześniejszym usunięciu FK)
4. DROP sekwencji
"""
from __future__ import annotations

from apex_export_to_md.renderers.base_renderer import BaseRenderer
from apex_export_to_md.models import ApexApp, DDLSchema
from apex_export_to_md.config import AppConfig


class RollbackRenderer(BaseRenderer):
    """Renderer generujący skrypt wycofania (DROP) wszystkich obiektów."""

    def render(self, app: ApexApp) -> str:
        """Generuj pełny skrypt rollback."""
        if not app.ddl_schema:
            return ""
        ddl = app.ddl_schema
        lines: list[str] = []

        lines.append("-- ============================================================")
        lines.append(f"-- SKRYPT WYCOFANIA (ROLLBACK) — {app.name} (ID: {app.id})")
        lines.append("-- Usuwa WSZYSTKIE obiekty utworzone przez skrypt migracyjny.")
        lines.append("-- Uruchom na użytkowniku zalogowanym do docelowego schematu.")
        lines.append("-- UWAGA: Operacja NIEODWRACALNA — dane zostaną utracone!")
        lines.append("-- ============================================================")
        lines.append("")

        # ---- SEKCJA 1: Usunięcie FK (aby umożliwić DROP TABLE) ----
        fk_lines = self._render_drop_foreign_keys(ddl)
        if fk_lines:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 1: USUNIĘCIE KLUCZY OBCYCH")
            lines.append("-- ============================================================")
            lines.append("")
            lines.append(fk_lines)
            lines.append("")

        # ---- SEKCJA 2: DROP procedur i funkcji ----
        if ddl.procedures:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 2: USUNIĘCIE PROCEDUR I FUNKCJI")
            lines.append("-- ============================================================")
            lines.append("")
            for proc in reversed(ddl.procedures):
                proc_type = self._detect_proc_type(proc)
                lines.append(f'DROP {proc_type} "{proc.name}";')
            lines.append("")

        # ---- SEKCJA 3: DROP pakietów ----
        if ddl.packages:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 3: USUNIĘCIE PAKIETÓW")
            lines.append("-- ============================================================")
            lines.append("")
            seen_pkgs: set[str] = set()
            for pkg in reversed(ddl.packages):
                if pkg.name not in seen_pkgs:
                    seen_pkgs.add(pkg.name)
                    lines.append(f'DROP PACKAGE "{pkg.name}";')
            lines.append("")

        # ---- SEKCJA 4: DROP widoków ----
        if ddl.views:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 4: USUNIĘCIE WIDOKÓW")
            lines.append("-- ============================================================")
            lines.append("")
            for view in reversed(ddl.views):
                lines.append(f'DROP VIEW "{view.name}";')
            lines.append("")

        # ---- SEKCJA 5: DROP tabel (w odwrotnej kolejności) ----
        if ddl.tables:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 5: USUNIĘCIE TABEL")
            lines.append("-- ============================================================")
            lines.append("")
            for table in reversed(ddl.tables):
                lines.append(f'DROP TABLE "{table.name}" CASCADE CONSTRAINTS PURGE;')
            lines.append("")

        # ---- SEKCJA 6: DROP sekwencji ----
        if ddl.sequences:
            lines.append("-- ============================================================")
            lines.append("-- SEKCJA 6: USUNIĘCIE SEKWENCJI")
            lines.append("-- ============================================================")
            lines.append("")
            for seq in reversed(ddl.sequences):
                lines.append(f'DROP SEQUENCE "{seq.name}";')
            lines.append("")

        # ---- COMMIT ----
        lines.append("COMMIT;")
        lines.append("")

        # ---- PODSUMOWANIE ----
        lines.append("-- ============================================================")
        lines.append("-- PODSUMOWANIE USUNIĘTYCH OBIEKTÓW")
        lines.append("-- ============================================================")
        lines.append(f"-- Sekwencje:  {len(ddl.sequences)}")
        lines.append(f"-- Tabele:     {len(ddl.tables)}")
        lines.append(f"-- Widoki:     {len(ddl.views)}")
        lines.append(f"-- Pakiety:    {len(ddl.packages)}")
        lines.append(f"-- Procedury:  {len(ddl.procedures)}")
        lines.append(f"-- RAZEM:      {len(ddl.sequences) + len(ddl.tables) + len(ddl.views) + len(ddl.packages) + len(ddl.procedures)}")
        lines.append("")
        lines.append("-- ============================================================")
        lines.append("-- KONIEC SKRYPTU WYCOFANIA")
        lines.append("-- ============================================================")

        return "\n".join(lines)

    def _render_drop_foreign_keys(self, ddl: DDLSchema) -> str:
        """Generuj ALTER TABLE DROP CONSTRAINT dla FK."""
        lines: list[str] = []
        for table in ddl.tables:
            for c in table.constraints:
                if c.type == "FOREIGN KEY" and c.name:
                    lines.append(
                        f'ALTER TABLE "{table.name}" DROP CONSTRAINT "{c.name}";'
                    )
        return "\n".join(lines)

    def _detect_proc_type(self, proc) -> str:
        """Wykryj typ procedury/funkcji na podstawie kodu."""
        if proc.code and proc.code.strip().upper().startswith("FUNCTION"):
            return "FUNCTION"
        return "PROCEDURE"
