# pylint: disable=redefined-outer-name
"""
Tests for HarvestService validation logic and CRUD operations.

All MongoDB access is mocked — no real database required.
"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

# conftest.py handles Django setup and heavy-dep mocking

from teramina.harvest.services.harvest_service import HarvestService
from teramina.harvest.schemas.harvest_schema import HarvestDataSchema


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _empty_harvest_data():
    return {
        "partial1": {"doc": "", "biomass": "", "revenue": ""},
        "partial2": {"doc": "", "biomass": "", "revenue": ""},
        "partial3": {"doc": "", "biomass": "", "revenue": ""},
        "final":    {"doc": "", "biomass": "", "revenue": ""},
    }

def _single_final(doc=80, biomass=1000.0, revenue=50_000_000):
    d = _empty_harvest_data()
    d["final"] = {"doc": doc, "biomass": biomass, "revenue": revenue}
    return d


@pytest.fixture()
def service():
    return HarvestService("test_cycle_001")


@pytest.fixture()
def mock_result_data_80_docs():
    """Fake ResultData with 80 rows, each row having total_biomass=2000."""
    rd = MagicMock()
    rd.result_data = [{"doc": i + 1, "total_biomass": 2000.0} for i in range(80)]
    return rd


# ── harvest_data_validation ────────────────────────────────────────────────────

class TestHarvestDataValidation:

    def test_all_empty_passes(self, service):
        """Fully empty harvest data (no-op) should not raise."""
        service.harvest_data_validation(
            current_doc=80,
            harvest_data=_empty_harvest_data(),
            is_simulation=True,
        )  # no exception

    def test_negative_doc_raises(self, service):
        data = _empty_harvest_data()
        data["final"] = {"doc": -1, "biomass": 500, "revenue": 1000}
        with pytest.raises(ValueError, match="lower than zero"):
            service.harvest_data_validation(80, data, is_simulation=True)

    def test_negative_biomass_raises(self, service):
        data = _empty_harvest_data()
        data["final"] = {"doc": 50, "biomass": -100.0, "revenue": 1000}
        with pytest.raises(ValueError, match="biomass"):
            service.harvest_data_validation(80, data, is_simulation=True)

    def test_duplicate_doc_raises(self, service):
        data = _empty_harvest_data()
        data["partial1"] = {"doc": 60, "biomass": 300, "revenue": 1000}
        data["partial2"] = {"doc": 60, "biomass": 200, "revenue": 1000}
        with pytest.raises(ValueError, match="60"):
            service.harvest_data_validation(80, data, is_simulation=True)

    def test_non_sequential_doc_raises(self, service):
        """DOC values must be monotonically increasing."""
        data = _empty_harvest_data()
        data["partial1"] = {"doc": 70, "biomass": 300, "revenue": 1000}
        data["partial2"] = {"doc": 50, "biomass": 200, "revenue": 1000}
        with pytest.raises(ValueError, match="not incremented"):
            service.harvest_data_validation(80, data, is_simulation=True)

    def test_non_numeric_doc_raises(self, service):
        data = _empty_harvest_data()
        data["final"] = {"doc": "abc", "biomass": 500, "revenue": 1000}
        with pytest.raises(ValueError):
            service.harvest_data_validation(80, data, is_simulation=True)

    def test_valid_partial_plus_final_simulation(self, service):
        data = _empty_harvest_data()
        data["partial1"] = {"doc": 60, "biomass": 400, "revenue": 5_000_000}
        data["final"]    = {"doc": 80, "biomass": 800, "revenue": 10_000_000}
        # is_simulation=True skips historical DB lookup — should not raise
        service.harvest_data_validation(80, data, is_simulation=True)


# ── get_harvest_record ─────────────────────────────────────────────────────────

class TestGetHarvestRecord:

    def test_no_record_returns_empty_rows(self, service):
        fake_result = MagicMock()
        fake_result.result_data = [{"doc": i + 1} for i in range(50)]

        with (
            patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR,
            patch("teramina.harvest.services.harvest_service.ResultData") as MockRD,
        ):
            MockHR.objects.return_value.first.return_value = None
            MockRD.objects.return_value.first.return_value = fake_result

            status, response = service.get_harvest_record()

        assert status == 200
        assert response.payload["rows"] == []
        assert response.payload["cycle_info"]["last_doc"] == 50

    def test_no_result_data_returns_400(self, service):
        with (
            patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR,
            patch("teramina.harvest.services.harvest_service.ResultData") as MockRD,
        ):
            MockHR.objects.return_value.first.return_value = None
            MockRD.objects.return_value.first.return_value = None

            status, response = service.get_harvest_record()

        assert status == 400
        assert "doesn't exist" in response.message.lower() or "cycle" in response.message.lower()


# ── delete_harvest_record ──────────────────────────────────────────────────────

class TestDeleteHarvestRecord:

    def test_delete_returns_200(self, service):
        with patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR:
            MockHR.objects.return_value.delete.return_value = None

            status, response = service.delete_harvest_record()

        assert status == 200
        assert "delete" in response.message.lower() or "successfully" in response.message.lower()

    def test_delete_calls_objects_filter(self, service):
        with patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR:
            MockHR.objects.return_value.delete.return_value = None
            service.delete_harvest_record()
            MockHR.objects.assert_called_once_with(cycle_id="test_cycle_001")


# ── get_harvest_recommendation ─────────────────────────────────────────────────

class TestGetHarvestRecommendation:

    def test_no_recommendation_returns_empty_payload(self, service):
        with (
            patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR,
            patch("teramina.harvest.services.harvest_service.HarvestRecommendation") as MockRec,
        ):
            MockHR.objects.return_value.first.return_value = None
            MockRec.objects.return_value.first.return_value = None

            status, response = service.get_harvest_recommendation()

        assert status == 200
        assert response.payload["rows"] == []

    def test_recommendation_exists_returns_table(self, service):
        fake_rec = MagicMock()
        fake_rec.harvest_data = {
            "partial1": {"doc": "", "biomass": "", "revenue": ""},
            "partial2": {"doc": "", "biomass": "", "revenue": ""},
            "partial3": {"doc": "", "biomass": "", "revenue": ""},
            "final": {"doc": 90, "biomass": 1500, "revenue": 80_000_000},
        }

        fake_fd = MagicMock()
        # Minimal dataframe-like result_data for harvest_table_formatter
        import pandas as pd
        fake_fd.result_data = [
            {
                "doc": i + 1,
                "adj_abw": 15.0,
                "harvest_biomass_kg": 800.0,
                "realized_revenue": 50_000_000.0,
                "profit": 20_000_000.0,
            }
            for i in range(100)
        ]

        with (
            patch("teramina.harvest.services.harvest_service.HarvestRecord") as MockHR,
            patch("teramina.harvest.services.harvest_service.HarvestRecommendation") as MockRec,
            patch("teramina.harvest.services.harvest_service.ForecastData") as MockFD,
        ):
            MockHR.objects.return_value.first.return_value = None
            MockRec.objects.return_value.first.return_value = fake_rec
            MockFD.objects.return_value.first.return_value = fake_fd

            status, response = service.get_harvest_recommendation()

        assert status == 200
        rows = response.payload.get("rows", [])
        # Final harvest should be present
        assert any(r["harvest_type"] == "final" for r in rows)
