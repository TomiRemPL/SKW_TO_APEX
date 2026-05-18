"""Moduł eksportu danych z Oracle — łączy się z bazą i pobiera dane tabel.

Używa pakietu `oracledb` (thin mode) do połączenia z Oracle Database.
Eksportuje dane tabel, wartości sekwencji i max wartości kolumn identity.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

try:
    import oracledb
except ImportError:
    oracledb = None  # type: ignore


@dataclass
class TableData:
    """Dane wyeksportowane z jednej tabeli."""
    table_name: str
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)


@dataclass
class SequenceValue:
    """Aktualna wartość sekwencji."""
    name: str
    current_value: int = 0


@dataclass
class ExportedData:
    """Pełne dane wyeksportowane z bazy."""
    tables: list[TableData] = field(default_factory=list)
    sequences: list[SequenceValue] = field(default_factory=list)
    identity_max_values: dict[str, int] = field(default_factory=dict)  # "TABLE.COLUMN" -> max


def _check_oracledb() -> None:
    """Sprawdź czy moduł oracledb jest dostępny."""
    if oracledb is None:
        raise ImportError(
            "Pakiet 'oracledb' nie jest zainstalowany. "
            "Zainstaluj go: pip install oracledb"
        )


def connect_to_db(connection_string: str) -> Any:
    """Nawiąż połączenie z bazą Oracle.

    Args:
        connection_string: Format: user/password@host:port/service_name
                          lub DSN string
    Returns:
        Obiekt połączenia oracledb.Connection
    """
    _check_oracledb()
    try:
        conn = oracledb.connect(connection_string)
        logger.info("Połączono z bazą Oracle.")
        return conn
    except Exception as e:
        logger.error("Błąd połączenia z bazą: %s", e)
        raise


def test_connection(connection_string: str) -> tuple[bool, str]:
    """Testuj połączenie z bazą Oracle.

    Returns:
        Tuple (sukces: bool, komunikat: str)
    """
    _check_oracledb()
    try:
        conn = oracledb.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.close()
        conn.close()
        return True, "Połączenie udane."
    except Exception as e:
        return False, f"Błąd: {e}"


def export_table_data(conn: Any, table_name: str) -> TableData:
    """Wyeksportuj wszystkie wiersze z tabeli.

    Args:
        conn: Aktywne połączenie oracledb
        table_name: Nazwa tabeli

    Returns:
        Obiekt TableData z kolumnami i wierszami
    """
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM "{table_name}"')
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        logger.info("Tabela %s: %d wierszy", table_name, len(rows))
        return TableData(
            table_name=table_name,
            columns=columns,
            rows=[list(row) for row in rows],
        )
    except Exception as e:
        logger.warning("Błąd odczytu tabeli %s: %s", table_name, e)
        return TableData(table_name=table_name)
    finally:
        cursor.close()


def get_sequence_value(conn: Any, seq_name: str) -> int:
    """Pobierz ostatnią wartość sekwencji (LAST_NUMBER z user_sequences)."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT LAST_NUMBER FROM USER_SEQUENCES WHERE SEQUENCE_NAME = :name",
            {"name": seq_name},
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.warning("Nie można odczytać sekwencji %s: %s", seq_name, e)
        return 0
    finally:
        cursor.close()


def get_identity_max(conn: Any, table_name: str, column_name: str) -> int:
    """Pobierz MAX wartość kolumny identity z tabeli."""
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT NVL(MAX("{column_name}"), 0) FROM "{table_name}"')
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.warning("Nie można odczytać max %s.%s: %s", table_name, column_name, e)
        return 0
    finally:
        cursor.close()


def resolve_insert_order(tables: list[str], fk_deps: dict[str, list[str]]) -> list[str]:
    """Topologiczne sortowanie tabel wg zależności FK.

    Args:
        tables: Lista nazw tabel
        fk_deps: Słownik {tabela: [tabele_od_których_zależy]}

    Returns:
        Lista tabel posortowana — tabele bez zależności pierwsze
    """
    result: list[str] = []
    visited: set[str] = set()
    in_progress: set[str] = set()

    def visit(table: str) -> None:
        if table in visited:
            return
        if table in in_progress:
            # Cykl — dodaj na koniec
            return
        in_progress.add(table)
        for dep in fk_deps.get(table, []):
            if dep in tables:
                visit(dep)
        in_progress.discard(table)
        visited.add(table)
        result.append(table)

    for t in tables:
        visit(t)
    return result


def export_all_data(connection_string: str, ddl_schema: Any) -> ExportedData:
    """Eksportuj wszystkie dane z bazy na podstawie schematu DDL.

    Args:
        connection_string: Connection string Oracle
        ddl_schema: Obiekt DDLSchema z parsera

    Returns:
        Pełne dane eksportu
    """
    _check_oracledb()
    conn = connect_to_db(connection_string)
    exported = ExportedData()

    try:
        # Zbuduj mapę zależności FK
        fk_deps: dict[str, list[str]] = {}
        for table in ddl_schema.tables:
            deps = []
            for c in table.constraints:
                if c.type == "FOREIGN KEY" and c.ref_table:
                    deps.append(c.ref_table)
            fk_deps[table.name] = deps

        # Posortuj tabele topologicznie
        table_names = [t.name for t in ddl_schema.tables]
        ordered_tables = resolve_insert_order(table_names, fk_deps)

        # Eksportuj dane tabel
        for table_name in ordered_tables:
            table_data = export_table_data(conn, table_name)
            exported.tables.append(table_data)

        # Eksportuj wartości sekwencji
        for seq in ddl_schema.sequences:
            val = get_sequence_value(conn, seq.name)
            exported.sequences.append(SequenceValue(name=seq.name, current_value=val))

        # Eksportuj max wartości kolumn identity
        for table in ddl_schema.tables:
            for col in table.columns:
                if col.identity:
                    max_val = get_identity_max(conn, table.name, col.name)
                    exported.identity_max_values[f"{table.name}.{col.name}"] = max_val

    finally:
        conn.close()
        logger.info("Połączenie z bazą zamknięte.")

    return exported
