"""Testy parsera shared components."""
from apex_export_to_md.parser.shared_parser import (
    parse_lovs, parse_authorizations, parse_app_items,
    parse_build_options, parse_breadcrumbs, parse_acl_roles, parse_nav_lists,
    parse_app_definition,
)


def test_parse_lovs_table(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert len(lovs) == 3
    assert lovs[0].source_type == "Table / View"
    assert lovs[0].source_table == "B_AUDYT"
    assert lovs[0].return_column == "ID_PK_B_AUDYT"


def test_parse_lovs_sql(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert lovs[1].source_type == "SQL Query"
    assert "B_KONTROLA" in lovs[1].sql_query


def test_parse_lovs_static(sample_lovs_yaml):
    lovs = parse_lovs(sample_lovs_yaml)
    assert lovs[2].source_type == "Static Values"
    assert len(lovs[2].entries) == 2
    assert lovs[2].entries[0]["display"] == "Tak"


def test_parse_authorizations(sample_authorizations_yaml):
    auths = parse_authorizations(sample_authorizations_yaml)
    assert len(auths) == 2
    assert auths[0].type == "PL/SQL Function Returning Boolean"
    assert auths[0].code == "RETURN TRUE;"
    assert auths[1].type == "Is In Role or Group"
    assert auths[1].role_or_group == "Administrator"


def test_parse_app_definition(sample_app_yaml):
    name, app_id, alias = parse_app_definition(sample_app_yaml)
    assert name == "SKW_2_APEX"
    assert app_id == "160"
    assert alias == "START338"
