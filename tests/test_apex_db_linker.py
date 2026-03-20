"""Testy linkera APEX↔DB — wykrywanie powiązań."""
import pytest
from apex_export_to_md.linker.apex_db_linker import ApexDbLinker, ApexDbLink
from apex_export_to_md.models.apex_models import (
    ApexApp, ApexPage, Region, Process, LOV, Validation,
)
from apex_export_to_md.models.db_models import DbSchema, DbTable, DbView


@pytest.fixture
def db_schema():
    return DbSchema(
        tables=[
            DbTable(name="B_AUDYT"),
            DbTable(name="B_AUDYT_KONTROLA"),
            DbTable(name="B_KONTROLA"),
        ],
        views=[DbView(name="B_V_AUDYT_KONTROLE")],
    )


@pytest.fixture
def apex_app():
    return ApexApp(
        name="TEST", id="1", alias="T",
        pages=[
            ApexPage(
                id=1, name="Lista audytow",
                regions=[
                    Region(
                        name="Grid",
                        type="Interactive Grid",
                        source_table="B_AUDYT",
                    ),
                    Region(
                        name="SQL Region",
                        type="Classic Report",
                        source_sql="SELECT * FROM B_AUDYT_KONTROLA ak JOIN B_KONTROLA k ON ak.ID = k.ID",
                    ),
                ],
                processes=[
                    Process(
                        name="Save",
                        type="PL/SQL",
                        code="INSERT INTO B_AUDYT_KONTROLA VALUES (:P1_ID, :P2_ID, :APP_USER, SYSDATE);",
                    ),
                ],
                validations=[
                    Validation(
                        name="Check",
                        type="PL/SQL",
                        code="SELECT 1 FROM B_V_AUDYT_KONTROLE WHERE ID = :P1_ID",
                    ),
                ],
            ),
            ApexPage(
                id=2, name="Pusta strona",
                regions=[Region(name="Static", type="Static Content")],
            ),
        ],
        lovs=[
            LOV(name="LOV_KONTROLE", source_type="SQL Query",
                sql_query="SELECT REFERENCE_ID FROM B_KONTROLA WHERE STATUS != 'Deactive'"),
        ],
    )


class TestApexDbLinker:
    def test_link_region_source_table(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        page1_links = [l for l in links if l.page_id == 1]
        all_objects = set()
        for l in page1_links:
            all_objects.update(l.db_objects)
        assert "B_AUDYT" in all_objects

    def test_link_region_sql(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        page1_links = [l for l in links if l.page_id == 1]
        all_objects = set()
        for l in page1_links:
            all_objects.update(l.db_objects)
        assert "B_AUDYT_KONTROLA" in all_objects
        assert "B_KONTROLA" in all_objects

    def test_link_process_code(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        proc_links = [l for l in links if l.source_type == "process"]
        assert len(proc_links) > 0
        assert "B_AUDYT_KONTROLA" in proc_links[0].db_objects

    def test_link_validation(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        val_links = [l for l in links if l.source_type == "validation"]
        all_objects = set()
        for l in val_links:
            all_objects.update(l.db_objects)
        assert "B_V_AUDYT_KONTROLE" in all_objects

    def test_link_lov(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        lov_links = [l for l in links if l.source_type == "lov"]
        all_objects = set()
        for l in lov_links:
            all_objects.update(l.db_objects)
        assert "B_KONTROLA" in all_objects

    def test_empty_page_no_links(self, apex_app, db_schema):
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        page2_links = [l for l in links if l.page_id == 2]
        assert len(page2_links) == 0

    def test_no_false_positive_prefix(self, apex_app, db_schema):
        """B_AUDYT nie powinien matchować B_AUDYT_KONTROLA (word boundary)."""
        linker = ApexDbLinker(apex_app, db_schema)
        links = linker.find_links()
        grid_links = [l for l in links if l.source_name == "Grid"]
        assert len(grid_links) == 1
        assert grid_links[0].db_objects == ["B_AUDYT"]
