"""Testy parsera pliku SQL eksportu APEX (app_sql_parser)."""
from pathlib import Path

import pytest

from apex_export_to_md.models import AppMetadata
from apex_export_to_md.parser.app_sql_parser import (
    parse_app_sql_file,
    find_app_sql_file,
)


@pytest.fixture
def sample_sql_file(tmp_path: Path) -> Path:
    """Minimalny plik f*.sql z metadanymi aplikacji."""
    content = """\
prompt --application/set_environment
set define off verify off feedback off
--
-- Oracle APEX export file
--
-- Application Export:
--   Application:     160
--   Name:            SKW_2_APEX
--   Exported By:     TREMBIASZ
--     Pages:                     33
--       Items:                   57
--       Validations:              2
--       Processes:               32
--       Regions:                 82
--       Buttons:                 44
--       Dynamic Actions:         25
--     Shared Components:
--       Logic:
--         Build Options:          9
--       Navigation:
--         Lists:                  8
--       Security:
--         Authentication:         3
--       User Interface:
--         LOVs:                  14
--   Version:         24.2.10
--
begin
wwv_flow_imp.import_begin (
 p_version_yyyy_mm_dd=>'2024.11.30'
,p_release=>'24.2.10'
,p_default_workspace_id=>7655170844003451
,p_default_application_id=>160
,p_default_id_offset=>273343216679699556
,p_default_owner=>'DAW'
);
end;
/

prompt --application/create_application
begin
wwv_imp_workspace.create_flow(
 p_id=>wwv_flow.g_flow_id
,p_owner=>nvl(wwv_flow_application_install.get_schema,'DAW')
,p_name=>nvl(wwv_flow_application_install.get_application_name,'SKW_2_APEX')
,p_alias=>nvl(wwv_flow_application_install.get_application_alias,'START160')
,p_flow_language=>'pl'
,p_flow_version=>'Release 1.0'
,p_browser_cache=>'N'
 ,p_compatibility_mode=>'21.2'
 ,p_page_protection_enabled_y_n=>'Y'
 ,p_bookmark_checksum_function=>'SH512'
 ,p_exact_substitutions_only=>'Y'
 ,p_runtime_api_usage=>'T'
 ,p_security_scheme=>'MUST_NOT_BE_PUBLIC_USER'
 ,p_rejoin_existing_sessions=>'P'
 ,p_page_view_logging=>'YES'
 ,p_flow_status=>'AVAILABLE_W_EDIT_LINK'
 ,p_file_storage=>'DB'
 ,p_files_version=>13
 ,p_working_copy_created_by=>'TREMBIASZ'
 ,p_working_copy_name=>'tr_20260731'
,p_is_pwa=>'Y'
,p_pwa_is_installable=>'Y'
,p_pwa_is_push_enabled=>'Y'
,p_substitution_string_01=>'APP_NAME'
,p_substitution_value_01=>'SKW_2_APEX'
,p_substitution_string_02=>'APP_COPYRIGHT'
,p_substitution_value_02=>'Empowered by DAW ZAIT Team'
);
end;
/
"""
    sql_file = tmp_path / "f338.sql"
    sql_file.write_text(content, encoding="utf-8")
    return sql_file


def test_parsuje_metadane_z_naglowka(sample_sql_file: Path):
    """Parsuje ID, nazwę, eksportera i statystyki z nagłówka."""
    meta = parse_app_sql_file(sample_sql_file)
    assert meta is not None
    assert meta.app_id == "160"
    assert meta.app_name == "SKW_2_APEX"
    assert meta.exported_by == "TREMBIASZ"
    assert meta.pages_count == 33
    assert meta.items_count == 57
    assert meta.regions_count == 82
    assert meta.buttons_count == 44
    assert meta.dynamic_actions_count == 25
    assert meta.processes_count == 32
    assert meta.validations_count == 2


def test_parsuje_wersje_apex(sample_sql_file: Path):
    """Parsuje wersję APEX z bloku import_begin."""
    meta = parse_app_sql_file(sample_sql_file)
    assert meta is not None
    assert meta.apex_version == "24.2.10"
    assert meta.owner == "DAW"


def test_parsuje_create_flow(sample_sql_file: Path):
    """Parsuje parametry z bloku create_flow."""
    meta = parse_app_sql_file(sample_sql_file)
    assert meta is not None
    assert meta.alias == "START160"
    assert meta.language == "pl"
    assert meta.version == "Release 1.0"
    assert meta.is_pwa is True
    assert meta.pwa_installable is True
    assert meta.push_enabled is True
    assert meta.browser_cache is False


def test_parsuje_konfiguracje_techniczna(sample_sql_file: Path):
    """Parsuje ustawienia zgodności, bezpieczeństwa i wdrożenia."""
    meta = parse_app_sql_file(sample_sql_file)
    assert meta is not None
    assert meta.compatibility_mode == "21.2"
    assert meta.page_protection_enabled is True
    assert meta.bookmark_checksum_function == "SH512"
    assert meta.exact_substitutions_only is True
    assert meta.runtime_api_usage == "T"
    assert meta.security_scheme == "MUST_NOT_BE_PUBLIC_USER"
    assert meta.rejoin_existing_sessions == "P"
    assert meta.page_view_logging is True
    assert meta.flow_status == "AVAILABLE_W_EDIT_LINK"
    assert meta.file_storage == "DB"
    assert meta.files_version == 13
    assert meta.working_copy_name == "tr_20260731"
    assert meta.working_copy_created_by == "TREMBIASZ"


def test_parsuje_substitutions(sample_sql_file: Path):
    """Parsuje zmienne substytucyjne."""
    meta = parse_app_sql_file(sample_sql_file)
    assert meta is not None
    assert meta.substitutions == {
        "APP_NAME": "SKW_2_APEX",
        "APP_COPYRIGHT": "Empowered by DAW ZAIT Team",
    }
    assert meta.copyright == "Empowered by DAW ZAIT Team"


def test_find_app_sql_file(tmp_path: Path):
    """Znajduje plik f<number>.sql w katalogu."""
    (tmp_path / "f160.sql").write_text("-- test", encoding="utf-8")
    (tmp_path / "skw_DDL_1.sql").write_text("-- ddl", encoding="utf-8")
    result = find_app_sql_file(tmp_path)
    assert result is not None
    assert result.name == "f160.sql"


def test_find_app_sql_file_brak(tmp_path: Path):
    """Zwraca None gdy brak pliku f*.sql."""
    (tmp_path / "other.sql").write_text("-- test", encoding="utf-8")
    result = find_app_sql_file(tmp_path)
    assert result is None
