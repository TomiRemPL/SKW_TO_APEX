"""Współdzielone fixtures — przykładowe struktury YAML eksportu APEX."""
import pytest


@pytest.fixture
def sample_page_yaml() -> dict:
    """Minimalna strona użytkownika (wzór: DAW_LISTA_AUDYTOW)."""
    return {
        "id": 4,
        "identification": {
            "name": "DAW_LISTA_AUDYTOW",
            "alias": "DAW-LISTA-AUDYTOW",
            "title": "DAW_LISTA_AUDYTOW",
        },
        "appearance": {"page-mode": "Normal"},
        "security": {
            "authentication": "Page Requires Authentication",
            "page-access-protection": "Arguments Must Have Checksum",
        },
        "css": {"inline": ".highlight { color: red; }"},
        "regions": [
            {
                "identification": {
                    "name": "ListaAudytow",
                    "title": "Lista audytów",
                    "type": "Interactive Grid",
                },
                "source": {
                    "location": "Local Database",
                    "type": "Table / View",
                    "table-name": "B_AUDYT",
                },
                "layout": {
                    "sequence": 20,
                    "parent-region": "No Parent",
                    "slot": "BODY",
                },
                "attributes": {
                    "edit": {
                        "enabled": True,
                        "allowed-operations": ["Add Row", "Update Row", "Delete Row"],
                    },
                },
                "columns": [
                    {
                        "identification": {"column-name": "ID_PK_B_AUDYT", "type": "Hidden"},
                        "source": {
                            "database-column": "ID_PK_B_AUDYT",
                            "data-type": "NUMBER",
                            "primary-key": True,
                        },
                    },
                    {
                        "identification": {"column-name": "B_AUDYT_NUMER_AUDYTU", "type": "Link"},
                        "heading": {"heading": "Numer Audytu"},
                        "source": {
                            "database-column": "B_AUDYT_NUMER_AUDYTU",
                            "data-type": "VARCHAR2",
                            "primary-key": False,
                        },
                        "link": {"target": {"page": "6 # DAW_WYBOR_KONTROLI"}},
                    },
                ],
            },
        ],
        "page-items": [
            {
                "identification": {"name": "P4_FILTR_STATUS", "type": "Select List"},
                "label": {"label": "Status"},
                "list-of-values": {"list-of-values": "STATUS_AUDYTU # 123"},
                "source": {"type": "Null"},
            },
        ],
        "buttons": [
            {
                "identification": {"button-name": "UTWORZ_AUDYT"},
                "label": {"label": "Nowy audyt"},
                "behavior": {"action": "Submit Page"},
                "appearance": {"hot": True},
            },
        ],
        "processes": [
            {
                "identification": {"name": "Zapisz_Dane", "type": "Execute Code"},
                "source": {
                    "language": "PL/SQL",
                    "pl/sql-code": "BEGIN PKG_AUDYT.ZAPISZ(:P4_ID); END;",
                },
                "execution": {"point": "After Submit"},
                "server-side-condition": {"when-button-pressed": "SAVE # 999"},
            },
        ],
        "dynamic-actions": [
            {
                "identification": {"name": "Zmiana_statusu"},
                "when": {
                    "event": "Change",
                    "selection-type": "Item",
                    "item": "P4_STATUS",
                },
                "execution": {"event-scope": "Dynamic"},
                "actions": [
                    {
                        "identification": {"action": "Execute PL/SQL Code"},
                        "settings": {"pl/sql-code": "BEGIN NULL; END;"},
                        "affected-elements": {
                            "selection-type": "jQuery Selector",
                            "jquery-selector": "#region1",
                        },
                        "execution": {"fire-on-initialization": False},
                    },
                ],
            },
        ],
        "branches": [
            {
                "identification": {"name": "Go To Page 6"},
                "behavior": {
                    "type": "Page or URL (Redirect)",
                    "target": {"page": "6 # DAW_WYBOR_KONTROLI", "url": None},
                },
                "execution": {"point": "After Processing"},
                "server-side-condition": {"type": "Request = Value", "value": "SAVE"},
            },
        ],
        "validations": [
            {
                "identification": {"name": "Sprawdz_Numer"},
                "validation": {
                    "type": "PL/SQL Function Body",
                    "pl/sql-function-body": "RETURN :P4_NUMER IS NOT NULL;",
                },
            },
        ],
    }


@pytest.fixture
def sample_admin_page_yaml() -> dict:
    """Strona administracyjna (powinna być odfiltrowana)."""
    return {
        "id": 10000,
        "identification": {
            "name": "Administration",
            "alias": "ADMIN",
            "title": "Administration",
            "page-group": "Administration # 52840988022029242",
        },
        "appearance": {"page-mode": "Normal"},
        "security": {
            "authorization-scheme": "Administration Rights # 52839508229029280",
            "authentication": "Page Requires Authentication",
        },
    }


@pytest.fixture
def sample_lovs_yaml() -> list[dict]:
    """Przykładowe LOV-y trzech typów."""
    return [
        {
            "identification": {"name": "B_AUDYT.NUMER"},
            "source": {"type": "Table / View", "table-name": "B_AUDYT"},
            "column-mapping": {"return": "ID_PK_B_AUDYT", "display": "B_AUDYT_NUMER_AUDYTU"},
        },
        {
            "identification": {"name": "KONTROLE_SQL"},
            "source": {
                "type": "SQL Query",
                "sql-query": "SELECT id, name FROM B_KONTROLA WHERE active = 1",
            },
            "column-mapping": {"return": "id", "display": "name"},
        },
        {
            "identification": {"name": "TAK_NIE"},
            "source": {"type": "Static Values"},
            "entries": [
                {"entry": {"sequence": 1, "display": "Tak", "return": "1"}},
                {"entry": {"sequence": 2, "display": "Nie", "return": "0"}},
            ],
        },
    ]


@pytest.fixture
def sample_app_yaml() -> dict:
    """Główny plik aplikacji (f338.yaml)."""
    return {
        "id": 160,
        "identification": {"name": "SKW_2_APEX", "alias": "START338"},
    }


@pytest.fixture
def sample_authorizations_yaml() -> list[dict]:
    """Schematy autoryzacji."""
    return [
        {
            "identification": {"name": "AD Role"},
            "authorization-scheme": {"type": "PL/SQL Function Returning Boolean"},
            "settings": {"pl/sql-function-body": "RETURN TRUE;"},
        },
        {
            "identification": {"name": "Administration Rights"},
            "authorization-scheme": {"type": "Is In Role or Group"},
            "settings": {"type": "Application Role", "name(s)": "Administrator"},
        },
    ]
