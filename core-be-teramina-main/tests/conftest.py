# pylint: disable=redefined-outer-name
"""
Shared fixtures for Google Sheets integration tests.

All MongoDB access and Google API calls are mocked — no network or database
required. Tests run purely in-memory via mongomock + unittest.mock.
"""

import os
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is importable and Django is configured BEFORE any
# model or service import.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teramina.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "*")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/fake-creds.json")
os.environ.setdefault("MONGOATLAS_USER", "test")
os.environ.setdefault("MONGOATLAS_PASSWORD", "test")
os.environ.setdefault("MONGOATLAS_HOST", "localhost")
os.environ.setdefault("MONGOATLAS_DATABASE", "test_db")
os.environ.setdefault("GS_BUCKET_NAME", "test-bucket")
os.environ.setdefault("GS_PROJECT_ID", "test-project")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

# ---------------------------------------------------------------------------
# Stub heavy ML/vector dependencies that are not installed in test env.
# These modules are imported at module level in several services; replacing
# them with MagicMock prevents ImportError without affecting the logic we test.
# ---------------------------------------------------------------------------
for _mod in [
    "langchain",
    "langchain.vectorstores",
    "langchain.vectorstores.pinecone",
    "langchain.vectorstores.faiss",
    "langchain.embeddings",
    "langchain.embeddings.openai",
    "langchain.chat_models",
    "langchain.agents",
    "langchain.agents.openai_functions_agent",
    "langchain.agents.openai_functions_agent.base",
    "langchain.agents.agent_toolkits",
    "langchain.document_loaders",
    "langchain.chains",
    "pinecone",
    "pinecone_client",
    "faiss",
    "tiktoken",
    "openai",
    "fpdf",
    "prophet",
    "xgboost",
    "shap",
    "anthropic",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Must patch mongoengine.connect BEFORE settings.py runs it
import mongoengine
_orig_connect = mongoengine.connect
mongoengine.connect = lambda *a, **kw: _orig_connect("test_db", host="mongomock://localhost")

# Patch google.oauth2 Credentials before they're used in settings.py
_fake_creds = MagicMock()
_fake_creds.service_account_email = "test@test.iam.gserviceaccount.com"
with patch("google.oauth2.service_account.Credentials.from_service_account_file", return_value=_fake_creds):
    import django
    django.setup()

# Restore connect so in-test usage still works
mongoengine.connect = _orig_connect


@pytest.fixture(autouse=True)
def mock_google_creds():
    """Globally mock Google service account credential loading."""
    with patch("google.oauth2.service_account.Credentials.from_service_account_file") as mock:
        mock.return_value = _fake_creds
        yield mock


# ---------------------------------------------------------------------------
# Fixed IDs used across test fixtures
# ---------------------------------------------------------------------------
CYCLE_ID = "test_cycle_001"
USER_ID = "test_user_001"
FARM_ID = "test_farm_001"
POND_ID = "test_pond_001"
SPREADSHEET_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz_0123456789"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
START_DATE = datetime(2024, 1, 1)


# ---------------------------------------------------------------------------
# Mock Sheets API service
# ---------------------------------------------------------------------------

def _build_sheets_service(tab_data: dict | None = None):
    """
    Create a mock Google Sheets API service.

    tab_data: dict mapping "TAB!range" → list[list[str]] to return as values.
    """
    if tab_data is None:
        tab_data = {}

    service = MagicMock()

    def mock_get(**kwargs):
        """Simulate spreadsheets().values().get(spreadsheetId=..., range=...)."""
        req_range = kwargs.get("range", "")
        execute_mock = MagicMock()
        # Match on tab prefix
        matched = None
        for key, rows in tab_data.items():
            if req_range.startswith(key.split("!")[0]):
                matched = rows
                break
        execute_mock.execute.return_value = {"values": matched or []}
        return execute_mock

    def mock_append(**kwargs):
        execute_mock = MagicMock()
        execute_mock.execute.return_value = {}
        return execute_mock

    def mock_batch_update(**kwargs):
        execute_mock = MagicMock()
        execute_mock.execute.return_value = {}
        return execute_mock

    def mock_create(**kwargs):
        execute_mock = MagicMock()
        execute_mock.execute.return_value = {
            "spreadsheetId": SPREADSHEET_ID,
            "spreadsheetUrl": SPREADSHEET_URL,
        }
        return execute_mock

    values_mock = MagicMock()
    values_mock.get = mock_get
    values_mock.append = mock_append
    values_mock.batchUpdate = mock_batch_update

    spreadsheets_mock = MagicMock()
    spreadsheets_mock.values.return_value = values_mock
    spreadsheets_mock.create = mock_create

    service.spreadsheets.return_value = spreadsheets_mock

    return service


def _build_drive_service():
    """Create a mock Google Drive API service."""
    service = MagicMock()
    perms = MagicMock()
    create_mock = MagicMock()
    create_mock.execute.return_value = {"id": "perm_123"}
    perms.create.return_value = create_mock
    service.permissions.return_value = perms
    return service


# ---------------------------------------------------------------------------
# Sample sheet data
# ---------------------------------------------------------------------------

def _daily_log_rows():
    """3 rows of daily log data in the correct column layout (A..S)."""
    return [
        # date, doc, do_m, do_a, do_avg, temp_m, temp_a, temp_avg,
        # ph_m, ph_a, salinity, nh3, turbidity, feed_kg, feed_leftover,
        # feed_type, protein%, freq, notes
        ["2024-01-01", "1", "5.2", "6.1", "", "28", "30", "",
         "7.5", "7.8", "15", "0.1", "35", "10", "0.5",
         "Starter", "40", "4", "Good day"],
        ["02/01/2024", "", "4.8", "5.5", "", "27", "29", "",
         "7.6", "7.9", "16", "0.2", "30", "12", "1.0",
         "Grower", "38", "3", ""],
        ["2024-01-03", "3", "6.0", "6.5", "6.25", "29", "31", "30",
         "7.4", "7.7", "14", "0.15", "32", "15", "0.8",
         "Grower", "38", "4", "Rain"],
    ]


def _abw_rows():
    """2 ABW sampling rows."""
    return [
        # date, doc, sample_count, total_weight_g, abw, min, max, cv%, sampled_by, notes
        ["2024-01-07", "7", "30", "150", "5.0", "3.5", "6.5", "12.5", "Andi", "Week 1"],
        ["2024-01-14", "14", "30", "240", "8.0", "5.5", "10.5", "14.2", "Budi", "Week 2"],
    ]


def _cost_rows():
    """2 cost records."""
    return [
        # date, category, description, qty, unit, unit_price, total, vendor, notes
        ["2024-01-01", "Feed", "Starter feed", "100", "kg", "15000", "1500000", "PT Feed", ""],
        ["2024-01-05", "Chemical", "Probiotics", "5", "L", "50000", "250000", "CV Bio", ""],
    ]


def _harvest_rows():
    """1 partial harvest + 1 final harvest."""
    return [
        # date, doc, is_partial, biomass_kg, abw_g, sr%, bags, buyer, price/kg, notes
        ["2024-03-15", "75", "Y", "500", "15.5", "85", "10", "PT Buyer A", "65000", "Partial 1"],
        ["2024-04-01", "92", "N", "1200", "22.0", "80", "24", "PT Buyer B", "72000", "Final"],
    ]


def _mortality_rows():
    """2 mortality records."""
    return [
        # date, doc, dead_count, notes
        ["2024-01-05", "5", "12", "White feces"],
        ["2024-01-10", "10", "5", "Normal"],
    ]


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_cycle():
    """Fake Cycle document."""
    c = SimpleNamespace()
    c.id = CYCLE_ID
    c.name = "Test Cycle Jan-2024"
    c.start_date = START_DATE
    c.pond_id = POND_ID
    c.is_active = True
    return c


@pytest.fixture()
def mock_pond():
    """Fake Pond document."""
    p = SimpleNamespace()
    p.id = POND_ID
    p.name = "Pond A1"
    p.size = 1000
    p.depth = 1.5
    p.farm_id = FARM_ID
    return p


@pytest.fixture()
def mock_user():
    """Fake User document."""
    u = SimpleNamespace()
    u.id = USER_ID
    u.email = "farmer@test.com"
    u.name = "Test Farmer"
    return u


@pytest.fixture()
def sheets_service_empty():
    """Sheets API service that returns empty results for all tabs."""
    return _build_sheets_service({})


@pytest.fixture()
def sheets_service_full():
    """Sheets API service with sample data in all tabs."""
    return _build_sheets_service({
        "SETUP": [["Parameter", "Value"], ["Farm Name", "Test Farm"]],
        "DAILY_LOG": _daily_log_rows(),
        "ABW_SAMPLING": _abw_rows(),
        "COST": _cost_rows(),
        "HARVEST": _harvest_rows(),
        "MORTALITY": _mortality_rows(),
    })


@pytest.fixture()
def drive_service():
    """Mock Drive API service."""
    return _build_drive_service()


@pytest.fixture()
def sample_daily_rows():
    return _daily_log_rows()


@pytest.fixture()
def sample_abw_rows():
    return _abw_rows()


@pytest.fixture()
def sample_cost_rows():
    return _cost_rows()


@pytest.fixture()
def sample_harvest_rows():
    return _harvest_rows()


@pytest.fixture()
def sample_mortality_rows():
    return _mortality_rows()
