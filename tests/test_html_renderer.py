"""Testy renderera interaktywnego HTML."""
import json
import pytest
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.apex_models import ApexApp, ApexPage, Region
from apex_export_to_md.models.db_models import (
    DbSchema, DbTable, DbColumn, DbConstraint, DbView,
    DbPackage, DbSubprogram, DbSequence,
)
from apex_export_to_md.linker.apex_db_linker import ApexDbLink
from apex_export_to_md.renderers.html_renderer import HtmlRenderer


@pytest.fixture
def config():
    return AppConfig(author_name="Tomasz Rembiasz")


@pytest.fixture
def sample_app():
    return ApexApp(
        name="SKW_2_APEX", id="160", alias="START338",
        pages=[
            ApexPage(id=1, name="Home",
                     regions=[Region(name="R1", type="Grid", source_table="B_AUDYT")]),
        ],
    )


@pytest.fixture
def sample_schema():
    return DbSchema(
        tables=[
            DbTable(name="B_AUDYT",
                    columns=[DbColumn(name="ID", data_type="NUMBER")],
                    constraints=[DbConstraint(name="PK", constraint_type="PK", columns=["ID"])],
                    comment="Tabela audytow"),
            DbTable(name="B_ANKIETA",
                    constraints=[
                        DbConstraint(name="FK1", constraint_type="FK",
                                     columns=["FK_ID"], ref_table="B_AUDYT",
                                     ref_columns=["ID"]),
                    ]),
        ],
        views=[DbView(name="V1", comment="Widok")],
        packages=[DbPackage(name="PKG1")],
        sequences=[DbSequence(name="SEQ1")],
    )


@pytest.fixture
def sample_links():
    return [
        ApexDbLink(page_id=1, page_name="Home",
                   db_objects=["B_AUDYT"], source_type="region", source_name="R1"),
    ]


class TestHtmlRenderer:
    def test_produces_html(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_vis_js(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "<script" in html
        assert "const DATA" in html

    def test_branding_footer(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "Tomasz Rembiasz" in html
        assert "Claude" in html
        assert "apex_export_to_md" in html

    def test_branding_logo_svg(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "<svg" in html
        assert "TR" in html

    def test_app_name_in_header(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "SKW_2_APEX" in html

    def test_json_data_embedded(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert '"B_AUDYT"' in html
        assert '"B_ANKIETA"' in html

    def test_three_tabs(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "tab-diagram" in html or "Diagram" in html
        assert "tab-browser" in html or "Baza danych" in html
        assert "tab-map" in html or "APEX" in html

    def test_fk_edges_in_data(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "FK1" in html

    def test_error_codes_in_html_data(self, config, sample_app, sample_schema, sample_links):
        sample_schema.packages[0].error_codes = [(-20001, "Test error")]
        renderer = HtmlRenderer(config)
        html = renderer.render(sample_app, sample_schema, sample_links)
        assert "-20001" in html
        assert "Test error" in html

    def test_links_in_data(self, config, sample_app, sample_schema, sample_links):
        r = HtmlRenderer(config)
        html = r.render(sample_app, sample_schema, sample_links)
        assert "Home" in html
