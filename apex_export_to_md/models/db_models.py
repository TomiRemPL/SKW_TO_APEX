"""Modele danych bazy jako dataclasses.

Każda klasa odpowiada typowi obiektu w eksporcie DDL Oracle.
Pola odpowiadają wartościom wyekstrahowanym z plików SQL.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DbColumn:
    """Kolumna tabeli bazodanowej."""

    name: str
    data_type: str                    # np. "VARCHAR2(4000 CHAR)", "NUMBER(11,0)"
    nullable: bool = True
    default: str | None = None        # np. "'Otwarty'", "SYSDATE"
    identity: bool = False
    comment: str | None = None


@dataclass
class DbConstraint:
    """Constraint tabeli (PK, FK, UNIQUE, CHECK)."""

    name: str
    constraint_type: str              # "PK", "FK", "UQ", "CHK"
    columns: list[str] = field(default_factory=list)
    ref_table: str | None = None      # tylko FK
    ref_columns: list[str] = field(default_factory=list)  # tylko FK
    check_expression: str | None = None  # tylko CHK


@dataclass
class DbIndex:
    """Indeks tabeli."""

    name: str
    table_name: str
    columns: list[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class DbTable:
    """Tabela bazodanowa z kolumnami, constraint'ami i indeksami."""

    name: str
    columns: list[DbColumn] = field(default_factory=list)
    constraints: list[DbConstraint] = field(default_factory=list)
    indexes: list[DbIndex] = field(default_factory=list)
    comment: str | None = None


@dataclass
class DbView:
    """Widok bazodanowy."""

    name: str
    columns: list[str] = field(default_factory=list)
    sql: str = ""
    comment: str | None = None


@dataclass
class DbSequence:
    """Sekwencja Oracle."""

    name: str
    min_value: str | None = None
    max_value: str | None = None
    increment_by: str | None = None
    start_with: str | None = None
    cache: str | None = None
    nocache: bool = False


@dataclass
class DbParameter:
    """Parametr procedury/funkcji PL/SQL."""

    name: str
    data_type: str
    direction: str = "IN"             # "IN", "OUT", "IN OUT"
    description: str | None = None


@dataclass
class DbSubprogram:
    """Procedura lub funkcja w pakiecie PL/SQL."""

    name: str
    subprogram_type: str              # "PROCEDURE" lub "FUNCTION"
    parameters: list[DbParameter] = field(default_factory=list)
    return_type: str | None = None    # tylko dla FUNCTION
    description: str | None = None    # z komentarza nad procedurą/funkcją
    visibility: str = "public"        # "public" (w spec) lub "private" (tylko w body)


@dataclass
class DbPackage:
    """Pakiet PL/SQL — łączy specyfikację i body."""

    name: str
    spec_subprograms: list[DbSubprogram] = field(default_factory=list)
    body_subprograms: list[DbSubprogram] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    spec_source: str = ""             # kod specyfikacji
    body_source: str = ""             # kod body z komentarzami
    error_codes: list[tuple[int, str]] = field(default_factory=list)  # (kod, tekst) z RAISE_APPLICATION_ERROR


@dataclass
class DbSchema:
    """Kontener główny — pełny schemat bazy danych."""

    tables: list[DbTable] = field(default_factory=list)
    views: list[DbView] = field(default_factory=list)
    packages: list[DbPackage] = field(default_factory=list)
    sequences: list[DbSequence] = field(default_factory=list)
