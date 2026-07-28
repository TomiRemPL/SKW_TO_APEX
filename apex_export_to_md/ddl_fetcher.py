"""Moduł automatycznego pobierania DDL z bazy Oracle.

Wyszukuje obiekty bazy danych na podstawie keyword w komentarzach
i generuje kompletny plik DDL używając DBMS_METADATA.
"""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import oracledb
except ImportError:
    oracledb = None  # type: ignore


def _check_oracledb() -> None:
    """Sprawdź czy moduł oracledb jest dostępny."""
    if oracledb is None:
        raise ImportError(
            "Pakiet 'oracledb' nie jest zainstalowany. "
            "Zainstaluj go: pip install oracledb"
        )


def _sanitize_keyword(keyword: str) -> str:
    """Usuń znaki specjalne z keyword dla nazwy pliku."""
    return re.sub(r'[^\w\-]', '', keyword)


def _connect_to_db(connection_string: str) -> Any:
    """Nawiąż połączenie z bazą Oracle."""
    _check_oracledb()
    try:
        conn = oracledb.connect(connection_string)
        logger.info("Połączono z bazą Oracle (pobieranie DDL).")
        return conn
    except Exception as e:
        logger.error("Błąd połączenia z bazą: %s", e)
        raise


def _find_objects_by_keyword(conn: Any, keyword: str) -> dict[str, list[tuple[str, str]]]:
    """Znajdź wszystkie obiekty DB z keyword w komentarzu.

    Args:
        conn: Połączenie z bazą Oracle
        keyword: Keyword do wyszukania (np. */OnSite*/)

    Returns:
        Słownik {typ_obiektu: [(nazwa, owner), ...]}
    """
    cursor = conn.cursor()
    results: dict[str, list[tuple[str, str]]] = {
        'SEQUENCE': [],
        'TABLE': [],
        'INDEX': [],
        'VIEW': [],
        'PACKAGE': [],
        'PROCEDURE': [],
        'FUNCTION': [],
        'TRIGGER': [],
    }

    # Pobierz nazwę użytkownika (current schema)
    cursor.execute("SELECT USER FROM DUAL")
    current_user = cursor.fetchone()[0]

    # Pattern SQL dla keyword (case-insensitive)
    keyword_pattern = f"%{keyword}%"

    try:
        # 1. Tabele z keyword w komentarzu
        cursor.execute("""
            SELECT table_name, owner
            FROM ALL_TAB_COMMENTS
            WHERE table_type = 'TABLE'
              AND UPPER(comments) LIKE UPPER(:keyword)
              AND owner = :owner
        """, {"keyword": keyword_pattern, "owner": current_user})
        results['TABLE'] = cursor.fetchall()
        logger.info("Znaleziono %d tabel z keyword '%s'", len(results['TABLE']), keyword)

        # 2. Widoki z keyword w komentarzu
        cursor.execute("""
            SELECT table_name, owner
            FROM ALL_TAB_COMMENTS
            WHERE table_type = 'VIEW'
              AND UPPER(comments) LIKE UPPER(:keyword)
              AND owner = :owner
        """, {"keyword": keyword_pattern, "owner": current_user})
        results['VIEW'] = cursor.fetchall()
        logger.info("Znaleziono %d widoków z keyword '%s'", len(results['VIEW']), keyword)

        # 3. Sekwencje - sprawdź czy istnieją komentarze (ALL_MVIEW_COMMENTS lub custom)
        # Oracle nie ma standardowych komentarzy dla sekwencji, więc pominiemy filtrowanie
        # i pobierzemy wszystkie sekwencje użytkownika (można ulepszyć w przyszłości)
        # Alternatywa: użyć ALL_SEQUENCES z filtrem na nazwie (jeśli keyword jest w nazwie)
        cursor.execute("""
            SELECT sequence_name, sequence_owner
            FROM ALL_SEQUENCES
            WHERE sequence_owner = :owner
              AND UPPER(sequence_name) LIKE UPPER(:keyword)
        """, {"owner": current_user, "keyword": keyword_pattern})
        results['SEQUENCE'] = cursor.fetchall()
        logger.info("Znaleziono %d sekwencji pasujących do keyword", len(results['SEQUENCE']))

        # 4. Indeksy - dla tabel z keyword
        if results['TABLE']:
            table_names = [t[0] for t in results['TABLE']]
            placeholders = ','.join([f":t{i}" for i in range(len(table_names))])
            params = {f"t{i}": name for i, name in enumerate(table_names)}
            params['owner'] = current_user

            cursor.execute(f"""
                SELECT index_name, owner
                FROM ALL_INDEXES
                WHERE table_name IN ({placeholders})
                  AND owner = :owner
            """, params)
            results['INDEX'] = cursor.fetchall()
            logger.info("Znaleziono %d indeksów dla tabel z keyword", len(results['INDEX']))

        # 5. Pakiety - ALL_SOURCE nie ma komentarzy, więc użyjemy ALL_OBJECTS + nazwa
        cursor.execute("""
            SELECT object_name, owner
            FROM ALL_OBJECTS
            WHERE object_type = 'PACKAGE'
              AND owner = :owner
              AND UPPER(object_name) LIKE UPPER(:keyword)
        """, {"owner": current_user, "keyword": keyword_pattern})
        results['PACKAGE'] = cursor.fetchall()
        logger.info("Znaleziono %d pakietów pasujących do keyword", len(results['PACKAGE']))

        # 6. Procedury standalone
        cursor.execute("""
            SELECT object_name, owner
            FROM ALL_OBJECTS
            WHERE object_type = 'PROCEDURE'
              AND owner = :owner
              AND UPPER(object_name) LIKE UPPER(:keyword)
        """, {"owner": current_user, "keyword": keyword_pattern})
        results['PROCEDURE'] = cursor.fetchall()
        logger.info("Znaleziono %d procedur pasujących do keyword", len(results['PROCEDURE']))

        # 7. Funkcje standalone
        cursor.execute("""
            SELECT object_name, owner
            FROM ALL_OBJECTS
            WHERE object_type = 'FUNCTION'
              AND owner = :owner
              AND UPPER(object_name) LIKE UPPER(:keyword)
        """, {"owner": current_user, "keyword": keyword_pattern})
        results['FUNCTION'] = cursor.fetchall()
        logger.info("Znaleziono %d funkcji pasujących do keyword", len(results['FUNCTION']))

        # 8. Triggery - dla tabel z keyword
        if results['TABLE']:
            table_names = [t[0] for t in results['TABLE']]
            placeholders = ','.join([f":t{i}" for i in range(len(table_names))])
            params = {f"t{i}": name for i, name in enumerate(table_names)}
            params['owner'] = current_user

            cursor.execute(f"""
                SELECT trigger_name, owner
                FROM ALL_TRIGGERS
                WHERE table_name IN ({placeholders})
                  AND owner = :owner
            """, params)
            results['TRIGGER'] = cursor.fetchall()
            logger.info("Znaleziono %d triggerów dla tabel z keyword", len(results['TRIGGER']))

    except Exception as e:
        logger.error("Błąd wyszukiwania obiektów: %s", e)
        raise
    finally:
        cursor.close()

    return results


def _get_ddl(conn: Any, object_type: str, object_name: str, owner: str) -> str:
    """Pobierz DDL obiektu używając DBMS_METADATA.GET_DDL.

    Args:
        conn: Połączenie z bazą
        object_type: Typ obiektu (TABLE, VIEW, etc.)
        object_name: Nazwa obiektu
        owner: Owner obiektu

    Returns:
        String z DDL lub pusty string w przypadku błędu
    """
    cursor = conn.cursor()
    try:
        # Ustaw formatowanie DBMS_METADATA dla czytelnego wyjścia
        cursor.execute("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', true); END;")
        cursor.execute("BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', true); END;")

        # Pobierz DDL
        cursor.execute("""
            SELECT DBMS_METADATA.GET_DDL(:object_type, :object_name, :owner)
            FROM DUAL
        """, {"object_type": object_type, "object_name": object_name, "owner": owner})

        result = cursor.fetchone()
        if result and result[0]:
            # DBMS_METADATA zwraca CLOB
            ddl = result[0].read() if hasattr(result[0], 'read') else str(result[0])
            return ddl.strip()
        return ""
    except Exception as e:
        logger.warning("Nie można pobrać DDL dla %s %s.%s: %s", object_type, owner, object_name, e)
        return ""
    finally:
        cursor.close()


def _get_comments(conn: Any, table_name: str, owner: str) -> list[str]:
    """Pobierz komentarze dla tabeli i jej kolumn.

    Returns:
        Lista SQL statements z COMMENT ON
    """
    cursor = conn.cursor()
    comments: list[str] = []

    try:
        # Komentarz tabeli
        cursor.execute("""
            SELECT comments
            FROM ALL_TAB_COMMENTS
            WHERE table_name = :table_name AND owner = :owner
        """, {"table_name": table_name, "owner": owner})
        row = cursor.fetchone()
        if row and row[0]:
            comment_text = row[0].replace("'", "''")  # Escape single quotes
            comments.append(f"COMMENT ON TABLE \"{table_name}\" IS '{comment_text}';")

        # Komentarze kolumn
        cursor.execute("""
            SELECT column_name, comments
            FROM ALL_COL_COMMENTS
            WHERE table_name = :table_name AND owner = :owner AND comments IS NOT NULL
        """, {"table_name": table_name, "owner": owner})
        for row in cursor.fetchall():
            col_name, col_comment = row
            col_comment_escaped = col_comment.replace("'", "''")
            comments.append(f"COMMENT ON COLUMN \"{table_name}\".\"{col_name}\" IS '{col_comment_escaped}';")

    except Exception as e:
        logger.warning("Błąd pobierania komentarzy dla %s: %s", table_name, e)
    finally:
        cursor.close()

    return comments


def fetch_ddl_from_database(connection_string: str, keyword: str, output_dir: Path) -> tuple[bool, str]:
    """Główna funkcja pobierająca DDL z bazy Oracle.

    Args:
        connection_string: Connection string Oracle (user/pass@host:port/service)
        keyword: Keyword do wyszukania w komentarzach obiektów
        output_dir: Katalog wyjściowy dla pliku DDL

    Returns:
        Tuple (sukces: bool, ścieżka_pliku: str)
    """
    if not keyword:
        logger.error("Keyword jest pusty - nie można filtrować obiektów")
        return False, ""

    conn = None
    try:
        # Połącz z bazą
        conn = _connect_to_db(connection_string)

        # Znajdź obiekty z keyword
        logger.info("Wyszukiwanie obiektów z keyword '%s'...", keyword)
        objects = _find_objects_by_keyword(conn, keyword)

        # Sprawdź czy znaleziono jakiekolwiek obiekty
        total_objects = sum(len(obj_list) for obj_list in objects.values())
        if total_objects == 0:
            logger.warning("⚠ Keyword '%s' nie znalazł żadnych obiektów w bazie", keyword)
            return False, ""

        logger.info("Znaleziono łącznie %d obiektów do wyeksportowania", total_objects)

        # Generuj plik DDL
        output_dir.mkdir(parents=True, exist_ok=True)
        sanitized_keyword = _sanitize_keyword(keyword)
        output_file = output_dir / f"auto_ddl_{sanitized_keyword}.sql"

        logger.info("Generowanie pliku DDL: %s", output_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            # Nagłówek
            f.write("-- Automatycznie wygenerowany DDL\n")
            f.write(f"-- Keyword: {keyword}\n")
            f.write(f"-- Łącznie obiektów: {total_objects}\n")
            f.write("-- Data wygenerowania: " +
                   __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

            # Kolejność: Sekwencje → Tabele → Indeksy → Widoki → Pakiety → Procedury → Funkcje → Triggery
            object_order = ['SEQUENCE', 'TABLE', 'INDEX', 'VIEW', 'PACKAGE', 'PROCEDURE', 'FUNCTION', 'TRIGGER']

            for obj_type in object_order:
                obj_list = objects.get(obj_type, [])
                if not obj_list:
                    continue

                f.write(f"\n-- ============================================\n")
                f.write(f"-- {obj_type}S ({len(obj_list)})\n")
                f.write(f"-- ============================================\n\n")

                for obj_name, owner in obj_list:
                    logger.info("Pobieranie DDL: %s %s.%s", obj_type, owner, obj_name)

                    # Pobierz DDL
                    ddl = _get_ddl(conn, obj_type, obj_name, owner)
                    if ddl:
                        f.write(f"-- {obj_type}: {obj_name}\n")
                        f.write(ddl)
                        f.write("\n\n")

                        # Dla pakietów: pobierz również PACKAGE BODY
                        if obj_type == 'PACKAGE':
                            body_ddl = _get_ddl(conn, 'PACKAGE BODY', obj_name, owner)
                            if body_ddl:
                                f.write(f"-- PACKAGE BODY: {obj_name}\n")
                                f.write(body_ddl)
                                f.write("\n\n")

                    # Dla tabel: dodaj komentarze
                    if obj_type == 'TABLE':
                        comments = _get_comments(conn, obj_name, owner)
                        if comments:
                            f.write(f"-- Komentarze dla tabeli {obj_name}\n")
                            for comment_sql in comments:
                                f.write(comment_sql + "\n")
                            f.write("\n")

            f.write("\n-- Koniec automatycznie wygenerowanego DDL\n")

        logger.info("✓ Plik DDL wygenerowany pomyślnie: %s", output_file)
        return True, str(output_file)

    except Exception as e:
        logger.error("Błąd podczas pobierania DDL z bazy: %s", e)
        return False, ""

    finally:
        if conn:
            conn.close()
            logger.info("Połączenie z bazą zamknięte.")
