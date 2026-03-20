"""Testy modeli danych bazy — tworzenie i walidacja dataclasses."""
import pytest
from apex_export_to_md.models.db_models import (
    DbColumn, DbConstraint, DbIndex, DbTable, DbView,
    DbSequence, DbParameter, DbSubprogram, DbPackage, DbSchema,
)


class TestDbColumn:
    def test_create_minimal(self):
        col = DbColumn(name="ID", data_type="NUMBER")
        assert col.name == "ID"
        assert col.data_type == "NUMBER"
        assert col.nullable is True
        assert col.default is None
        assert col.identity is False
        assert col.comment is None

    def test_create_full(self):
        col = DbColumn(
            name="STATUS",
            data_type="VARCHAR2(20)",
            nullable=False,
            default="'Otwarty'",
            identity=False,
            comment="Status audytu",
        )
        assert col.nullable is False
        assert col.default == "'Otwarty'"
        assert col.comment == "Status audytu"

    def test_identity_column(self):
        col = DbColumn(name="ID_PK", data_type="NUMBER", identity=True, nullable=False)
        assert col.identity is True


class TestDbConstraint:
    def test_pk(self):
        c = DbConstraint(name="B_AUDYT_PK", constraint_type="PK", columns=["ID_PK_B_AUDYT"])
        assert c.constraint_type == "PK"
        assert c.ref_table is None

    def test_fk(self):
        c = DbConstraint(
            name="B_ANKIETA_B_AUDYT_FK",
            constraint_type="FK",
            columns=["ID_FK_B_AUDYT"],
            ref_table="B_AUDYT",
            ref_columns=["ID_PK_B_AUDYT"],
        )
        assert c.ref_table == "B_AUDYT"
        assert c.ref_columns == ["ID_PK_B_AUDYT"]

    def test_check(self):
        c = DbConstraint(
            name="B_AUDYT_STATUS_CHK",
            constraint_type="CHK",
            check_expression="STATUS_AUDYTU IN ('Otwarty', 'Zamrozony', 'Zakonczony')",
        )
        assert "Otwarty" in c.check_expression


class TestDbTable:
    def test_create_with_columns(self):
        t = DbTable(
            name="B_AUDYT",
            columns=[DbColumn(name="ID", data_type="NUMBER")],
            comment="Tabela audytow",
        )
        assert t.name == "B_AUDYT"
        assert len(t.columns) == 1
        assert t.comment == "Tabela audytow"

    def test_empty_table(self):
        t = DbTable(name="EMPTY")
        assert t.columns == []
        assert t.constraints == []
        assert t.indexes == []


class TestDbView:
    def test_create(self):
        v = DbView(
            name="B_V_AUDYT_KONTROLE",
            columns=["ID_FK_B_AUDYT", "REFERENCE_ID"],
            sql="SELECT ak.* FROM B_AUDYT_KONTROLA ak",
            comment="Widok kontroli",
        )
        assert v.name == "B_V_AUDYT_KONTROLE"
        assert len(v.columns) == 2


class TestDbSequence:
    def test_create(self):
        s = DbSequence(name="DAW_SEQ_B_C_ANAKIETA_PK", start_with="1203", increment_by="1")
        assert s.start_with == "1203"


class TestDbSubprogram:
    def test_procedure(self):
        p = DbSubprogram(
            name="UTWORZ_AUDYT",
            subprogram_type="PROCEDURE",
            parameters=[
                DbParameter(name="p_numer_audytu", data_type="VARCHAR2", direction="IN"),
                DbParameter(name="p_id_audytu", data_type="NUMBER", direction="OUT"),
            ],
            description="Tworzenie nowego audytu",
        )
        assert len(p.parameters) == 2
        assert p.visibility == "public"

    def test_private_procedure(self):
        p = DbSubprogram(
            name="POBIERZ_AUDYT",
            subprogram_type="PROCEDURE",
            visibility="private",
        )
        assert p.visibility == "private"

    def test_function(self):
        f = DbSubprogram(
            name="SPRAWDZ_UPRAWNIENIA",
            subprogram_type="FUNCTION",
            return_type="VARCHAR2",
        )
        assert f.return_type == "VARCHAR2"


class TestDbPackage:
    def test_create(self):
        pkg = DbPackage(
            name="PKG_AUDYT",
            spec_subprograms=[
                DbSubprogram(name="UTWORZ_AUDYT", subprogram_type="PROCEDURE"),
            ],
            body_subprograms=[
                DbSubprogram(name="UTWORZ_AUDYT", subprogram_type="PROCEDURE"),
                DbSubprogram(name="POBIERZ_AUDYT", subprogram_type="PROCEDURE", visibility="private"),
            ],
            constants=["C_STATUS_OTWARTY CONSTANT VARCHAR2(20) := 'Otwarty'"],
            spec_source="PACKAGE PKG_AUDYT AS ...",
            body_source="PACKAGE BODY PKG_AUDYT AS ...",
        )
        assert len(pkg.spec_subprograms) == 1
        assert len(pkg.body_subprograms) == 2


class TestDbSchema:
    def test_create_empty(self):
        s = DbSchema()
        assert s.tables == []
        assert s.views == []

    def test_create_full(self):
        s = DbSchema(
            tables=[DbTable(name="T1")],
            views=[DbView(name="V1")],
            packages=[DbPackage(name="P1")],
            sequences=[DbSequence(name="S1")],
        )
        assert len(s.tables) == 1
        assert len(s.views) == 1
