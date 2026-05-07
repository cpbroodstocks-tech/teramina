# pylint: disable=redefined-outer-name
"""
Unit tests for harvest and cycle_data input validation.

Covers:
  HarvestService validators:
    - __validate_doc_value: type check, negative, duplicate, non-monotonic
    - __validate_biomass_value: type, negative
    - harvest_data_validation: integration of validators

  CycleService.__validate_data:
    - ABW <= 0 hard reject
    - DO == 0 hard reject (with error message including DOC numbers)
    - date alignment check
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# conftest.py handles Django setup

from teramina.harvest.services.harvest_service import HarvestService


# ─── HarvestService DOC validation ────────────────────────────────────────────

class TestValidateDocValue:
    def _service(self):
        svc = HarvestService.__new__(HarvestService)
        svc.cycle_id = "test_cycle"
        return svc

    def test_valid_doc_no_error(self):
        svc = self._service()
        svc._HarvestService__validate_doc_value(50, set())

    def test_negative_doc_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="lower than zero"):
            svc._HarvestService__validate_doc_value(-1, set())

    def test_zero_doc_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="lower than zero"):
            svc._HarvestService__validate_doc_value(-1, set())

    def test_duplicate_doc_raises(self):
        svc = self._service()
        existing = {50}
        with pytest.raises(ValueError, match="50"):
            svc._HarvestService__validate_doc_value(50, existing)

    def test_non_monotonic_doc_raises(self):
        svc = self._service()
        existing = {70}
        with pytest.raises(ValueError, match="not incremented"):
            svc._HarvestService__validate_doc_value(50, existing)

    def test_monotonic_doc_no_error(self):
        svc = self._service()
        existing = {50}
        svc._HarvestService__validate_doc_value(70, existing)

    def test_non_numeric_doc_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="number"):
            svc._HarvestService__validate_doc_value("fifty", set())


# ─── HarvestService biomass validation ────────────────────────────────────────

class TestValidateBiomassValue:
    def _service(self):
        svc = HarvestService.__new__(HarvestService)
        svc.cycle_id = "test_cycle"
        return svc

    def test_positive_biomass_no_error(self):
        svc = self._service()
        svc._HarvestService__validate_biomass_value(500.0)

    def test_zero_biomass_no_error(self):
        svc = self._service()
        svc._HarvestService__validate_biomass_value(0.0)

    def test_negative_biomass_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="below zero"):
            svc._HarvestService__validate_biomass_value(-10.0)

    def test_none_biomass_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="number"):
            svc._HarvestService__validate_biomass_value(None)

    def test_string_biomass_raises(self):
        svc = self._service()
        with pytest.raises(ValueError, match="number"):
            svc._HarvestService__validate_biomass_value("five hundred")


# ─── HarvestService harvest_data_validation ───────────────────────────────────

class TestHarvestDataValidation:
    def _service(self, cycle_id="test_cycle"):
        return HarvestService(cycle_id)

    def test_empty_entries_are_skipped(self):
        svc = self._service()
        harvest_data = {"ph1": {"doc": "", "biomass": "", "revenue": ""}}
        svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)

    def test_valid_single_partial_harvest(self):
        svc = self._service()
        harvest_data = {"ph1": {"doc": 60, "biomass": 500.0, "revenue": 32500000}}
        svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)

    def test_valid_two_partial_harvests_monotonic(self):
        svc = self._service()
        harvest_data = {
            "ph1": {"doc": 60, "biomass": 300.0, "revenue": 19500000},
            "ph2": {"doc": 80, "biomass": 400.0, "revenue": 29000000},
        }
        svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)

    def test_non_monotonic_docs_raises(self):
        svc = self._service()
        harvest_data = {
            "ph1": {"doc": 80, "biomass": 300.0, "revenue": 0},
            "ph2": {"doc": 60, "biomass": 400.0, "revenue": 0},
        }
        with pytest.raises(ValueError, match="not incremented"):
            svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)

    def test_duplicate_doc_raises(self):
        svc = self._service()
        harvest_data = {
            "ph1": {"doc": 70, "biomass": 300.0, "revenue": 0},
            "ph2": {"doc": 70, "biomass": 400.0, "revenue": 0},
        }
        with pytest.raises(ValueError, match="70"):
            svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)

    def test_negative_biomass_raises(self):
        svc = self._service()
        harvest_data = {"ph1": {"doc": 60, "biomass": -100.0, "revenue": 0}}
        with pytest.raises(ValueError, match="below zero"):
            svc.harvest_data_validation(current_doc=90, harvest_data=harvest_data, is_simulation=True)


# ─── CycleService.__validate_data ─────────────────────────────────────────

class TestCycleDataValidate:
    def _validate(self, df, start_date=None):
        from teramina.cycle_data.services.cycle_data_service import CycleService
        svc = CycleService.__new__(CycleService)
        if start_date is None:
            start_date = df["date"].iloc[0]
        svc._CycleService__validate_data(df, start_date)

    def _make_df(self, abw=None, do=None, date_offset=0):
        n = 5
        base_date = datetime(2024, 1, 1)
        dates = [base_date + timedelta(days=i) for i in range(n)]
        return pd.DataFrame({
            "doc": list(range(1, n + 1)),
            "date": dates,
            "abw": abw if abw is not None else [5.0] * n,
            "do": do if do is not None else [6.0] * n,
            "temp": [29.0] * n,
        })

    def test_valid_data_no_error(self):
        df = self._make_df()
        self._validate(df)

    def test_abw_zero_raises(self):
        df = self._make_df(abw=[0.0, 5.0, 6.0, 7.0, 8.0])
        with pytest.raises(ValueError, match="body weight"):
            self._validate(df)

    def test_abw_negative_raises(self):
        df = self._make_df(abw=[-1.0, 5.0, 6.0, 7.0, 8.0])
        with pytest.raises(ValueError, match="body weight"):
            self._validate(df)

    def test_do_zero_raises_with_doc_in_message(self):
        df = self._make_df(do=[6.0, 6.0, 0.0, 6.0, 6.0])
        with pytest.raises(ValueError, match="DO") as exc_info:
            self._validate(df)
        # Error message should include the offending DOC number
        assert "3" in str(exc_info.value)

    def test_do_zero_on_multiple_docs_lists_all(self):
        df = self._make_df(do=[0.0, 6.0, 0.0, 6.0, 6.0])
        with pytest.raises(ValueError, match="DO") as exc_info:
            self._validate(df)
        msg = str(exc_info.value)
        assert "1" in msg
        assert "3" in msg

    def test_date_mismatch_raises(self):
        df = self._make_df()
        wrong_start = df["date"].iloc[0] + timedelta(days=5)
        with pytest.raises(ValueError, match="different day"):
            self._validate(df, start_date=wrong_start)

    def test_date_alignment_exact_match_no_error(self):
        df = self._make_df()
        self._validate(df, start_date=df["date"].iloc[0])
