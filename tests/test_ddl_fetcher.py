"""Testy modułu ddl_fetcher.py — automatyczne pobieranie DDL z Oracle."""
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from apex_export_to_md.ddl_fetcher import (
    _sanitize_keyword,
    _find_objects_by_keyword,
    _get_ddl,
    _get_comments,
    fetch_ddl_from_database,
)


def test_sanitize_keyword():
    """Sprawdza sanityzację keyword dla nazw plików."""
    assert _sanitize_keyword("*/OnSite*/") == "OnSite"
    assert _sanitize_keyword("HR-Module") == "HR-Module"  # Myślnik jest dozwolony w nazwach plików
    assert _sanitize_keyword("test_123") == "test_123"
    assert _sanitize_keyword("@#$%Special!") == "Special"


@patch("apex_export_to_md.ddl_fetcher.oracledb")
def test_find_objects_by_keyword(mock_oracledb):
    """Sprawdza wyszukiwanie obiektów po keyword."""
    # Mock połączenia i cursora
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock zapytań SQL
    mock_cursor.fetchone.return_value = ["TEST_USER"]  # SELECT USER
    mock_cursor.fetchall.side_effect = [
        [("TABLE1", "TEST_USER"), ("TABLE2", "TEST_USER")],  # Tabele
        [("VIEW1", "TEST_USER")],  # Widoki
        [("SEQ1", "TEST_USER")],  # Sekwencje
        [("IDX1", "TEST_USER")],  # Indeksy
        [("PKG1", "TEST_USER")],  # Pakiety
        [("PROC1", "TEST_USER")],  # Procedury
        [("FUNC1", "TEST_USER")],  # Funkcje
        [("TRG1", "TEST_USER")],  # Triggery
    ]

    results = _find_objects_by_keyword(mock_conn, "*/OnSite*/")

    assert len(results["TABLE"]) == 2
    assert len(results["VIEW"]) == 1
    assert len(results["SEQUENCE"]) == 1
    assert len(results["INDEX"]) == 1
    assert len(results["PACKAGE"]) == 1
    assert len(results["PROCEDURE"]) == 1
    assert len(results["FUNCTION"]) == 1
    assert len(results["TRIGGER"]) == 1


@patch("apex_export_to_md.ddl_fetcher.oracledb")
def test_get_ddl(mock_oracledb):
    """Sprawdza pobieranie DDL obiektu."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock CLOB DDL
    mock_clob = MagicMock()
    mock_clob.read.return_value = "CREATE TABLE TEST_TABLE (ID NUMBER);"
    mock_cursor.fetchone.return_value = [mock_clob]

    ddl = _get_ddl(mock_conn, "TABLE", "TEST_TABLE", "TEST_USER")

    assert "CREATE TABLE TEST_TABLE" in ddl
    assert mock_cursor.execute.call_count >= 3  # SET_TRANSFORM_PARAM x2 + GET_DDL


@patch("apex_export_to_md.ddl_fetcher.oracledb")
def test_get_comments(mock_oracledb):
    """Sprawdza pobieranie komentarzy dla tabeli."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock komentarzy
    mock_cursor.fetchone.return_value = ["Table comment with */OnSite*/ keyword"]
    mock_cursor.fetchall.return_value = [
        ("COL1", "Column 1 comment"),
        ("COL2", "Column 2 comment"),
    ]

    comments = _get_comments(mock_conn, "TEST_TABLE", "TEST_USER")

    assert len(comments) == 3  # 1 table + 2 columns
    assert "COMMENT ON TABLE" in comments[0]
    assert "COMMENT ON COLUMN" in comments[1]
    assert "COMMENT ON COLUMN" in comments[2]


@patch("apex_export_to_md.ddl_fetcher._connect_to_db")
@patch("apex_export_to_md.ddl_fetcher._find_objects_by_keyword")
@patch("apex_export_to_md.ddl_fetcher._get_ddl")
@patch("builtins.open", new_callable=mock_open)
def test_fetch_ddl_from_database_success(mock_file, mock_get_ddl, mock_find_objects, mock_connect):
    """Sprawdza pomyślne pobieranie DDL z bazy."""
    # Mock połączenia
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    # Mock znalezionych obiektów
    mock_find_objects.return_value = {
        "SEQUENCE": [("SEQ1", "TEST_USER")],
        "TABLE": [("TABLE1", "TEST_USER")],
        "INDEX": [],
        "VIEW": [("VIEW1", "TEST_USER")],
        "PACKAGE": [],
        "PROCEDURE": [],
        "FUNCTION": [],
        "TRIGGER": [],
    }

    # Mock DDL
    mock_get_ddl.return_value = "CREATE TABLE TABLE1 (ID NUMBER);"

    output_dir = Path("_data")
    success, file_path = fetch_ddl_from_database(
        "user/pass@host:1521/service",
        "*/OnSite*/",
        output_dir,
    )

    assert success is True
    assert "auto_ddl_OnSite.sql" in file_path
    mock_conn.close.assert_called_once()


@patch("apex_export_to_md.ddl_fetcher._connect_to_db")
@patch("apex_export_to_md.ddl_fetcher._find_objects_by_keyword")
def test_fetch_ddl_from_database_no_objects(mock_find_objects, mock_connect):
    """Sprawdza przypadek, gdy keyword nie znalazł obiektów."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    # Brak obiektów
    mock_find_objects.return_value = {
        "SEQUENCE": [],
        "TABLE": [],
        "INDEX": [],
        "VIEW": [],
        "PACKAGE": [],
        "PROCEDURE": [],
        "FUNCTION": [],
        "TRIGGER": [],
    }

    output_dir = Path("_data")
    success, file_path = fetch_ddl_from_database(
        "user/pass@host:1521/service",
        "*/NotFound*/",
        output_dir,
    )

    assert success is False
    assert file_path == ""
    mock_conn.close.assert_called_once()


def test_fetch_ddl_from_database_empty_keyword():
    """Sprawdza walidację pustego keyword."""
    output_dir = Path("_data")
    success, file_path = fetch_ddl_from_database(
        "user/pass@host:1521/service",
        "",
        output_dir,
    )

    assert success is False
    assert file_path == ""


@patch("apex_export_to_md.ddl_fetcher._connect_to_db")
def test_fetch_ddl_from_database_connection_error(mock_connect):
    """Sprawdza obsługę błędu połączenia."""
    mock_connect.side_effect = Exception("Connection failed")

    output_dir = Path("_data")
    success, file_path = fetch_ddl_from_database(
        "user/pass@invalid:1521/service",
        "*/OnSite*/",
        output_dir,
    )

    assert success is False
    assert file_path == ""
