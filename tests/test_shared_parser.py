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


def test_parse_nav_lists(sample_nav_lists_yaml):
    nav_lists = parse_nav_lists(sample_nav_lists_yaml)
    assert len(nav_lists) == 1
    assert nav_lists[0].name == "Navigation Menu"
    assert len(nav_lists[0].entries) == 2
    assert nav_lists[0].entries[0]["label"] == "DAW_LISTA_AUDYTOW"
    assert nav_lists[0].entries[0]["target_page"] == 4
    assert nav_lists[0].entries[1]["label"] == "DAW_IMPORT_KONTROLI"
    assert nav_lists[0].entries[1]["target_page"] == 5


def test_parse_app_items(sample_app_items_yaml):
    items = parse_app_items(sample_app_items_yaml)
    assert len(items) == 2
    assert items[0].name == "B_APP_ID_AUDYT"
    assert items[0].scope == "Application"
    assert items[1].name == "G_FIRSTNAME"
    assert items[1].scope == "Global"


def test_parse_build_options(sample_build_options_yaml):
    options = parse_build_options(sample_build_options_yaml)
    assert len(options) == 2
    assert options[0].name == "Commented Out"
    assert options[0].status == "Exclude"
    assert options[1].name == "Feature: Access Control"
    assert options[1].status == "Include"


def test_parse_breadcrumbs(sample_breadcrumbs_yaml):
    breadcrumbs = parse_breadcrumbs(sample_breadcrumbs_yaml)
    assert len(breadcrumbs) == 1
    assert breadcrumbs[0].name == "Breadcrumb"
    assert len(breadcrumbs[0].entries) == 2
    assert breadcrumbs[0].entries[0]["name"] == "DAW_LISTA_AUDYTOW"
    assert breadcrumbs[0].entries[0]["page_number"] == 4
    assert breadcrumbs[0].entries[1]["name"] == "Home"
    assert breadcrumbs[0].entries[1]["page_number"] == 1


def test_parse_acl_roles(sample_acl_roles_yaml):
    roles = parse_acl_roles(sample_acl_roles_yaml)
    assert len(roles) == 2
    assert roles[0].name == "Administrator"
    assert roles[0].static_id == "ADMINISTRATOR"
    assert roles[1].name == "Contributor"
    assert roles[1].static_id == "CONTRIBUTOR"
