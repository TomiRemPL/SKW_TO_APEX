"""Moduł automatycznego pobierania DDL z bazy Oracle.

Wyszukuje obiekty bazy danych na podstawie keyword: tabele i widoki po
komentarzu (COMMENT ON), pakiety/procedury/funkcje po keyword w komentarzu
kodu źródłowego, sekwencje na podstawie DEFAULT kolumn i triggerów tabel.
Generuje kompletny plik DDL używając DBMS_METADATA.
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


def _extract_comment_text(source_text: str) -> str:
    """Wyciągnij tekst komentarzy SQL/PLSQL (-- oraz /* ... */) z kodu źródłowego.

    Używane do wyszukiwania keyword tylko w komentarzach kodu pakietów,
    procedur i funkcji (nie w treści logiki, żeby uniknąć fałszywych trafień).
    """
    parts: list[str] = []
    for match in re.finditer(r'/\*.*?\*/', source_text, re.DOTALL):
        parts.append(match.group(0))
    for line in source_text.splitlines():
        idx = line.find('--')
        if idx != -1:
            parts.append(line[idx:])
    return "\n".join(parts)


def _find_code_objects_by_comment_keyword(
    conn: Any, owner: str, keyword: str, source_types: tuple[str, ...]
) -> set[str]:
    """Znajdź nazwy obiektów kodu (PACKAGE/PACKAGE BODY/PROCEDURE/FUNCTION),
    których komentarz w kodzie źródłowym zawiera keyword.

    Dla PACKAGE sprawdzane są niezależnie SPEC i BODY (source_types może
    zawierać oba typy) — wystarczy, że keyword wystąpi w jednym z nich.
    """
    cursor = conn.cursor()
    keyword_upper = keyword.upper()
    names: set[str] = set()
    try:
        placeholders = ",".join(f":t{i}" for i in range(len(source_types)))
        params: dict[str, str] = {"owner": owner}
        for i, source_type in enumerate(source_types):
            params[f"t{i}"] = source_type

        cursor.execute(f"""
            SELECT name, text
            FROM ALL_SOURCE
            WHERE owner = :owner AND type IN ({placeholders})
            ORDER BY name, line
        """, params)

        grouped: dict[str, list[str]] = {}
        for name, text in cursor.fetchall():
            grouped.setdefault(name, []).append(text or "")

        for name, lines in grouped.items():
            comment_text = _extract_comment_text("".join(lines))
            if keyword_upper in comment_text.upper():
                names.add(name)
    finally:
        cursor.close()
    return names


def _extract_sequence_names(text: str) -> set[str]:
    """Wyciągnij nazwy sekwencji z odwołań SEQ.NEXTVAL w tekście SQL/PLSQL."""
    return {
        match.group(1).upper()
        for match in re.finditer(r'"?(\w+)"?\s*\.\s*NEXTVAL', text, re.IGNORECASE)
    }


def _find_sequences_used_by_tables(
    conn: Any, owner: str, table_names: list[str]
) -> list[tuple[str, str]]:
    """Znajdź sekwencje używane przez podane tabele.

    Sprawdza zarówno DEFAULT kolumn (np. nowoczesny wzorzec
    "DEFAULT seq.NEXTVAL"), jak i treść triggerów powiązanych z tabelą
    (starszy wzorzec: trigger BEFORE INSERT wywołujący seq.NEXTVAL).
    """
    if not table_names:
        return []

    cursor = conn.cursor()
    try:
        placeholders = ",".join(f":t{i}" for i in range(len(table_names)))
        params = {f"t{i}": name for i, name in enumerate(table_names)}
        params["owner"] = owner

        seq_names: set[str] = set()

        cursor.execute(f"""
            SELECT data_default
            FROM ALL_TAB_COLUMNS
            WHERE owner = :owner AND table_name IN ({placeholders})
              AND data_default IS NOT NULL
        """, params)
        for (data_default,) in cursor.fetchall():
            if data_default:
                seq_names |= _extract_sequence_names(str(data_default))

        cursor.execute(f"""
            SELECT trigger_body
            FROM ALL_TRIGGERS
            WHERE owner = :owner AND table_name IN ({placeholders})
        """, params)
        for (trigger_body,) in cursor.fetchall():
            if trigger_body:
                seq_names |= _extract_sequence_names(str(trigger_body))

        if not seq_names:
            return []

        seq_names_list = sorted(seq_names)
        seq_placeholders = ",".join(f":s{i}" for i in range(len(seq_names_list)))
        seq_params = {f"s{i}": name for i, name in enumerate(seq_names_list)}
        seq_params["owner"] = owner
        cursor.execute(f"""
            SELECT sequence_name, sequence_owner
            FROM ALL_SEQUENCES
            WHERE sequence_owner = :owner AND sequence_name IN ({seq_placeholders})
        """, seq_params)
        return cursor.fetchall()
    finally:
        cursor.close()


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

        # 3. Sekwencje - wykryte na podstawie DEFAULT kolumn i triggerów tabel z keyword
        table_names_for_seq = [t[0] for t in results['TABLE']]
        results['SEQUENCE'] = _find_sequences_used_by_tables(conn, current_user, table_names_for_seq)
        logger.info("Znaleziono %d sekwencji używanych przez tabele z keyword", len(results['SEQUENCE']))

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

        # 5. Pakiety - keyword w komentarzu kodu (SPEC lub BODY, niezależnie)
        package_names = _find_code_objects_by_comment_keyword(
            conn, current_user, keyword, ('PACKAGE', 'PACKAGE BODY')
        )
        results['PACKAGE'] = [(name, current_user) for name in sorted(package_names)]
        logger.info("Znaleziono %d pakietów z keyword '%s' w komentarzu kodu", len(results['PACKAGE']), keyword)

        # 6. Procedury standalone - keyword w komentarzu kodu
        procedure_names = _find_code_objects_by_comment_keyword(
            conn, current_user, keyword, ('PROCEDURE',)
        )
        results['PROCEDURE'] = [(name, current_user) for name in sorted(procedure_names)]
        logger.info("Znaleziono %d procedur z keyword '%s' w komentarzu kodu", len(results['PROCEDURE']), keyword)

        # 7. Funkcje - keyword w komentarzu kodu
        function_names = _find_code_objects_by_comment_keyword(
            conn, current_user, keyword, ('FUNCTION',)
        )
        results['FUNCTION'] = [(name, current_user) for name in sorted(function_names)]
        logger.info("Znaleziono %d funkcji z keyword '%s' w komentarzu kodu", len(results['FUNCTION']), keyword)

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

                        # Dla pakietów: pobierz PACKAGE BODY tylko jeśli GET_DDL('PACKAGE')
                        # go nie zawiera (Oracle 12c+ zwraca spec+body razem w jednym wywołaniu)
                        if obj_type == 'PACKAGE' and 'PACKAGE BODY' not in ddl.upper():
                            body_ddl = _get_ddl(conn, 'PACKAGE_BODY', obj_name, owner)
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
