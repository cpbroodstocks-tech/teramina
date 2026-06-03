"""E2E tests for the Google Sheets integration (service layer)."""
import pytest
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError

from tests.conftest import (
    CYCLE_ID, USER_ID, SPREADSHEET_ID, SPREADSHEET_URL, START_DATE,
    _build_sheets_service, _build_drive_service,
    _daily_log_rows, _abw_rows, _cost_rows, _harvest_rows, _mortality_rows,
)

from teramina.google_sheets.services.sheet_service import (
    SheetService, _normalize_date, _safe_float, _safe_int, _safe_str,
    _auto_fill_doc, _col, _upsert_result_data, _backfill_row_ids,
)
from teramina.google_sheets.models.sheet_integration_model import SheetIntegration


# ── Helper utilities tests ────────────────────────────────────────────────

class TestNormalizeDate:
    def test_iso(self):
        assert _normalize_date("2024-01-15") == "2024-01-15"

    def test_dd_mm_yyyy_slash(self):
        assert _normalize_date("15/01/2024") == "2024-01-15"

    def test_dd_mm_yyyy_dash(self):
        assert _normalize_date("15-01-2024") == "2024-01-15"

    def test_dd_mon_yyyy(self):
        assert _normalize_date("15-Jan-2024") == "2024-01-15"

    def test_dd_mon_yy(self):
        assert _normalize_date("15-Jan-24") == "2024-01-15"

    def test_empty(self):
        assert _normalize_date("") is None
        assert _normalize_date(None) is None
        assert _normalize_date("N/A") is None

    def test_unparseable_returns_none(self):
        # Unparseable dates are rejected (None), not passed through silently.
        assert _normalize_date("not-a-date") is None
        assert _normalize_date("32/13/2024") is None


class TestSafeConversions:
    def test_float_valid(self):
        assert _safe_float("3.14") == 3.14

    def test_float_empty(self):
        assert _safe_float("") is None
        assert _safe_float("N/A") is None
        assert _safe_float("-") is None

    def test_float_default(self):
        assert _safe_float("bad", default=0.0) == 0.0

    def test_int_valid(self):
        assert _safe_int("42") == 42
        assert _safe_int("3.7") == 3

    def test_int_empty(self):
        assert _safe_int("") is None

    def test_str(self):
        assert _safe_str("  hello ") == "hello"
        assert _safe_str(None) == ""
        assert _safe_str("") == ""


class TestAutoFillDoc:
    def test_computes_doc(self):
        assert _auto_fill_doc("2024-01-10", datetime(2024, 1, 1)) == 10

    def test_day_one(self):
        assert _auto_fill_doc("2024-01-01", datetime(2024, 1, 1)) == 1

    def test_invalid(self):
        assert _auto_fill_doc("", datetime(2024, 1, 1)) is None
        assert _auto_fill_doc("2024-01-01", None) is None


class TestCol:
    def test_valid(self):
        assert _col(["a", "b", "c"], 1) == "b"

    def test_out_of_bounds(self):
        assert _col(["a"], 5) is None
        assert _col(["a"], 5, "X") == "X"


class TestRowIdBackfill:
    def test_writes_only_blank_row_id_cells(self):
        svc = _build_sheets_service({
            "DAILY_LOG": [
                ["2024-01-01"] + [""] * 19 + [""],
                ["2024-01-02"] + [""] * 19 + ["DAILY_LOG-4"],
            ],
            "ABW_SAMPLING": [["2024-01-01"] + [""] * 9 + [""]],
            "MORTALITY": [["2024-01-01", "", "", "", ""]],
            "COST": [["2024-01-01", "Feed", "Starter", "", "", "", "", "", "", ""]],
            "HARVEST": [["2024-01-01", "", "", "", "", "", "", "", "", "", ""]],
        })
        batch_update = MagicMock()
        batch_update.return_value.execute.return_value = {}
        svc.spreadsheets.return_value.values.return_value.batchUpdate = batch_update

        count = _backfill_row_ids(svc, SPREADSHEET_ID)

        assert count == 5
        data = batch_update.call_args.kwargs["body"]["data"]
        assert data == [
            {"range": "DAILY_LOG!U3", "values": [["DAILY_LOG-3"]]},
            {"range": "ABW_SAMPLING!K3", "values": [["ABW_SAMPLING-3"]]},
            {"range": "COST!J3", "values": [["COST-3"]]},
            {"range": "HARVEST!K3", "values": [["HARVEST-3"]]},
            {"range": "MORTALITY!E3", "values": [["MORTALITY-3"]]},
        ]


# ── UpsertResultData tests ────────────────────────────────────────────────

class TestUpsertResultData:
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    def test_creates_new_doc(self, MockCycleData):
        MockCycleData.objects.return_value.first.return_value = None
        new_doc = MagicMock()
        new_doc.save.return_value = new_doc
        MockCycleData.return_value = new_doc

        rows = [{"date": "2024-01-01", "do_avg": 5.5}]
        result = _upsert_result_data(None, CYCLE_ID, rows)
        assert result is new_doc

    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    def test_merges_existing(self, MockCycleData):
        existing = MagicMock()
        existing.result_data = [{"date": "2024-01-01", "do_avg": 5.0, "ph_morning": 7.5}]
        MockCycleData.objects.return_value.first.return_value = existing

        rows = [{"date": "2024-01-01", "do_avg": 6.0}]
        _upsert_result_data(existing, CYCLE_ID, rows)

        merged = existing.result_data[0]
        assert merged["do_avg"] == 6.0
        assert merged["ph_morning"] == 7.5  # preserved

    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    def test_appends_new_date(self, MockCycleData):
        existing = MagicMock()
        existing.result_data = [{"date": "2024-01-01", "do_avg": 5.0}]
        MockCycleData.objects.return_value.first.return_value = existing

        rows = [{"date": "2024-01-02", "do_avg": 6.0}]
        _upsert_result_data(existing, CYCLE_ID, rows)
        assert len(existing.result_data) == 2


# ── Connect tests ─────────────────────────────────────────────────────────

class TestConnect:
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_connect_success(self, MockIntegration, mock_get_svc):
        svc = _build_sheets_service({"SETUP": [["P", "V"]]})
        mock_get_svc.return_value = svc
        MockIntegration.objects.return_value.first.return_value = None
        mock_save = MagicMock()
        MockIntegration.return_value = mock_save

        code, body = SheetService.connect(USER_ID, CYCLE_ID, SPREADSHEET_ID)
        assert code == 200
        assert body.payload["spreadsheet_id"] == SPREADSHEET_ID

    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_connect_access_denied(self, mock_get_svc):
        """After bug fix: HttpError from Sheets API returns 400."""
        svc = MagicMock()
        resp = MagicMock()
        resp.status = 403
        error = HttpError(resp, b"forbidden")
        svc.spreadsheets().values().get().execute.side_effect = error
        mock_get_svc.return_value = svc

        code, body = SheetService.connect(USER_ID, CYCLE_ID, "bad_id")
        assert code == 400
        assert "Cannot access" in body.message

    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_connect_updates_existing(self, MockIntegration, mock_get_svc):
        svc = _build_sheets_service({"SETUP": [["P", "V"]]})
        mock_get_svc.return_value = svc
        existing = MagicMock()
        MockIntegration.objects.return_value.first.return_value = existing

        code, _ = SheetService.connect(USER_ID, CYCLE_ID, SPREADSHEET_ID)
        assert code == 200
        assert existing.spreadsheet_id == SPREADSHEET_ID
        assert existing.is_active is True
        existing.save.assert_called_once()


# ── Disconnect tests ──────────────────────────────────────────────────────

class TestDisconnect:
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_disconnect_success(self, MockIntegration):
        integration = MagicMock()
        MockIntegration.objects.return_value.first.return_value = integration

        code, body = SheetService.disconnect(CYCLE_ID)
        assert code == 200
        assert integration.is_active is False

    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_disconnect_not_found(self, MockIntegration):
        MockIntegration.objects.return_value.first.return_value = None
        code, body = SheetService.disconnect(CYCLE_ID)
        assert code == 400


# ── GetStatus tests ───────────────────────────────────────────────────────

class TestGetStatus:
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_status_no_integration(self, MockIntegration):
        MockIntegration.objects.return_value.first.return_value = None
        code, body = SheetService.get_status(CYCLE_ID)
        assert code == 200
        assert body.payload["is_active"] is False

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_status_active(self, MockIntegration, MockSyncLog):
        integration = MagicMock()
        integration.spreadsheet_id = SPREADSHEET_ID
        integration.spreadsheet_url = SPREADSHEET_URL
        integration.is_active = True
        integration.last_synced = datetime(2024, 1, 15)
        integration.last_status = "ok"
        integration.last_error = ""
        integration.rows_synced = 42
        integration.last_sync_log_id = None
        MockIntegration.objects.return_value.first.return_value = integration
        MockSyncLog.objects.return_value.first.return_value = None

        code, body = SheetService.get_status(CYCLE_ID)
        assert code == 200
        assert body.payload["is_active"] is True
        assert body.payload["rows_synced"] == 42

    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_status_old_integration_without_sync_fields(self, MockIntegration):
        integration = SimpleNamespace(
            spreadsheet_id=SPREADSHEET_ID,
            spreadsheet_url=SPREADSHEET_URL,
            is_active=True,
            last_synced=None,
            last_status="ok",
            last_error=None,
            rows_synced=0,
            last_sync_log_id=None,
        )
        MockIntegration.objects.return_value.first.return_value = integration

        code, body = SheetService.get_status(CYCLE_ID)

        assert code == 200
        assert body.payload["active_sync_id"] is None
        assert body.payload["last_sync_id"] is None
        assert body.payload["tab_summaries"] == []

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_status_includes_latest_log_observability_fields(self, MockIntegration, MockSyncLog):
        integration = SimpleNamespace(
            spreadsheet_id=SPREADSHEET_ID,
            spreadsheet_url=SPREADSHEET_URL,
            is_active=True,
            last_synced=None,
            last_status="partial",
            last_error="COST: forbidden",
            last_error_category="google_auth",
            rows_synced=0,
            active_sync_id=None,
            last_sync_log_id=UUID("12345678-1234-5678-1234-567812345678"),
        )
        log = SimpleNamespace(
            rows_per_second=12.5,
            error_category="google_auth",
            tab_summaries=[
                SimpleNamespace(
                    tab="COST",
                    processed=0,
                    inserted=0,
                    updated=0,
                    deleted=0,
                    skipped=0,
                    rejected=0,
                    error="forbidden",
                    error_category="google_auth",
                )
            ],
        )
        MockIntegration.objects.return_value.first.return_value = integration
        MockSyncLog.objects.return_value.first.return_value = log

        code, body = SheetService.get_status(CYCLE_ID)

        assert code == 200
        assert body.payload["rows_per_second"] == 12.5
        assert body.payload["error_category"] == "google_auth"
        assert body.payload["tab_summaries"][0]["error_category"] == "google_auth"


# ── SyncCycle tests ───────────────────────────────────────────────────────

def _base_sync_patches():
    """Common set of patches for sync_cycle tests."""
    return [
        patch("teramina.google_sheets.services.sheet_service.SheetSyncLog"),
        patch("teramina.google_sheets.services.sheet_service.FeedRealization"),
        patch("teramina.google_sheets.services.sheet_service.HarvestRecord"),
        patch("teramina.google_sheets.services.sheet_service.CostData"),
        patch("teramina.google_sheets.services.sheet_service.CycleData"),
        patch("teramina.google_sheets.services.sheet_service.Cycle"),
        patch("teramina.google_sheets.services.sheet_service.SheetIntegration"),
        patch("teramina.google_sheets.services.sheet_service._get_sheets_service"),
    ]


class TestSyncCycle:
    def _make_integration(self):
        i = MagicMock()
        i.spreadsheet_id = SPREADSHEET_ID
        i.is_active = True
        i.last_status = "pending"
        i.rows_synced = 0
        i.last_sync_log_id = None
        return i

    def _make_cycle(self):
        c = MagicMock()
        c.id = CYCLE_ID
        c.start_date = START_DATE
        c.pond_id = "pond1"
        return c

    def _make_empty_db(self, MockCycleData, MockCostData, MockHarvest, MockFeed):
        MockCycleData.objects.return_value.first.return_value = None
        cd_new = MagicMock()
        cd_new.result_data = []
        cd_new.save.return_value = cd_new
        MockCycleData.return_value = cd_new
        MockCostData.objects.return_value.first.return_value = None
        MockCostData.return_value = MagicMock()
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_full_sync(self, mock_get_svc, MockIntegration, MockCycle,
                       MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog):
        svc = _build_sheets_service({
            "DAILY_LOG": _daily_log_rows(),
            "ABW_SAMPLING": _abw_rows(),
            "COST": _cost_rows(),
            "HARVEST": _harvest_rows(),
            "MORTALITY": _mortality_rows(),
        })
        mock_get_svc.return_value = svc

        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)
        summary = result["summary"]

        assert summary["DAILY_LOG"]["inserted"] == 3
        assert summary["DAILY_LOG"]["rejected"] == 0
        assert summary["ABW_SAMPLING"]["inserted"] == 2
        assert summary["COST"]["inserted"] == 2
        assert summary["HARVEST"]["inserted"] == 2
        assert summary["MORTALITY"]["inserted"] == 2
        assert result["status"] == "ok"
        assert integration.last_status == "ok"

    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_sync_no_integration(self, MockIntegration, MockCycle):
        MockIntegration.objects.return_value.first.return_value = None
        result = SheetService.sync_cycle(CYCLE_ID)
        assert "error" in result

    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_sync_no_cycle(self, MockIntegration, MockCycle):
        MockIntegration.objects.return_value.first.return_value = self._make_integration()
        MockCycle.objects.return_value.first.return_value = None
        result = SheetService.sync_cycle(CYCLE_ID)
        assert "error" in result

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_date_normalization(self, mock_get_svc, MockIntegration,
                                     MockCycle, MockCycleData, MockCostData,
                                     MockHarvest, MockFeed, MockSyncLog):
        """DD/MM/YYYY format should be normalized."""
        svc = _build_sheets_service({
            "DAILY_LOG": [["15/01/2024", "", "5.0", "6.0"]],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)
        assert result["summary"]["DAILY_LOG"]["inserted"] == 1
        assert result["summary"]["DAILY_LOG"]["rejected"] == 0

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_auto_doc_computation(self, mock_get_svc, MockIntegration,
                                       MockCycle, MockCycleData, MockCostData,
                                       MockHarvest, MockFeed, MockSyncLog):
        """DOC should be auto-computed when missing."""
        svc = _build_sheets_service({
            "DAILY_LOG": [["2024-01-10", "", "5.0"]],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()

        saved_rows = []

        def capture_init(**kwargs):
            saved_rows.append(kwargs.get("result_data", []))
            m = MagicMock()
            m.result_data = kwargs.get("result_data", [])
            m.save.return_value = m
            return m

        MockCycleData.objects.return_value.first.return_value = None
        MockCycleData.side_effect = capture_init
        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        SheetService.sync_cycle(CYCLE_ID)
        assert len(saved_rows) > 0
        assert saved_rows[0][0]["doc"] == 10  # Jan 10 - Jan 1 + 1

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_empty_sheet(self, mock_get_svc, MockIntegration, MockCycle,
                              MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog):
        """Empty sheet should result in zero rows and status ok."""
        svc = _build_sheets_service({})
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)
        for tab in ["DAILY_LOG", "ABW_SAMPLING", "COST", "HARVEST", "MORTALITY"]:
            assert tab in result["summary"]
            assert result["summary"][tab].get("rejected", 0) == 0

    # ── New edge case tests (Task 6) ──────────────────────────────────────

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_malformed_date_produces_rejected_row(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        """A row with an unparseable date must appear in rejected_rows with reason=invalid_date."""
        svc = _build_sheets_service({
            "DAILY_LOG": [
                ["not-a-date", "1", "5.0", "6.0"],   # malformed
                ["2024-01-02", "2", "5.5", "6.5"],   # valid
            ],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        feedback_batch_update = MagicMock()
        feedback_batch_update.return_value.execute.return_value = {}
        svc.spreadsheets.return_value.values.return_value.batchUpdate = feedback_batch_update
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["DAILY_LOG"]["rejected"] == 1
        assert result["summary"]["DAILY_LOG"]["inserted"] == 1

        rejected = result["rejected_rows"]
        assert len(rejected) >= 1
        date_rejections = [r for r in rejected if r["reason"] == "invalid_date"]
        assert len(date_rejections) == 1
        assert date_rejections[0]["tab"] == "DAILY_LOG"
        assert date_rejections[0]["field"] == "date"
        assert date_rejections[0]["raw_value"] == "not-a-date"
        assert date_rejections[0]["row_number"] == 3  # row 1-2 are headers
        feedback_data = (
            svc.spreadsheets.return_value
            .values.return_value
            .batchUpdate.call_args.kwargs["body"]["data"]
        )
        assert feedback_data == [{
            "range": "DAILY_LOG!W3:X3",
            "values": [["ERROR", "date: invalid_date"]],
        }]

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_nh3_hard_failure_produces_rejected_row(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        """NH3=99 (above hard_max=50) must be rejected with reason hard_failure:nh3."""
        # A full DAILY_LOG row: date, doc, do_m, do_a, do_avg, temp_m, temp_a, temp_avg,
        # ph_m, ph_a, salinity, nh3, turbidity, feed_kg, leftover, type, prot%, freq, notes
        bad_row = ["2024-01-01", "1", "5.0", "6.0", "", "28", "30", "",
                   "7.5", "7.8", "15", "99.0", "35", "10", "0.5",
                   "Starter", "40", "4", ""]
        good_row = ["2024-01-02", "2", "5.5", "6.5", "", "27", "29", "",
                    "7.6", "7.9", "16", "0.2", "30", "12", "1.0",
                    "Grower", "38", "3", ""]
        svc = _build_sheets_service({
            "DAILY_LOG": [bad_row, good_row],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        # Bad row should be rejected; good row inserted
        assert result["summary"]["DAILY_LOG"]["rejected"] == 1
        assert result["summary"]["DAILY_LOG"]["inserted"] == 1

        rejected = result["rejected_rows"]
        nh3_failures = [r for r in rejected if "hard_failure:nh3" in r.get("reason", "")]
        assert len(nh3_failures) == 1
        assert nh3_failures[0]["tab"] == "DAILY_LOG"
        assert nh3_failures[0]["field"] == "nh3"
        assert float(nh3_failures[0]["raw_value"]) == 99.0

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_partial_sync_on_tab_exception(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        """If one tab raises an exception, status=partial; other tabs still processed."""
        svc = _build_sheets_service({
            "DAILY_LOG": _daily_log_rows(),
            "ABW_SAMPLING": _abw_rows(),
            "COST": _cost_rows(),
            "HARVEST": _harvest_rows(),
            "MORTALITY": _mortality_rows(),
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        # Make CostData raise during save to simulate a tab error
        MockCostData.side_effect = RuntimeError("DB unavailable")

        result = SheetService.sync_cycle(CYCLE_ID)

        # COST should have error; others should succeed
        assert "error" in result["summary"]["COST"]
        assert "error" not in result["summary"]["DAILY_LOG"]
        assert result["status"] == "partial"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_cost_invalid_price_flagged(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        """A COST row with a non-numeric unit_price is flagged in rejected_rows (row still imported)."""
        cost_rows = [
            # date, category, description, qty, unit, unit_price, total, vendor, notes
            # "fifteen thousand" is a genuine user error (intended number, wrong format)
            ["2024-01-01", "Feed", "Starter feed", "100", "kg", "fifteen thousand", "1500000", "PT Feed", ""],
            ["2024-01-05", "Chemical", "Probiotics", "5", "L", "50000", "250000", "CV Bio", ""],
        ]
        svc = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "HARVEST": [], "MORTALITY": [],
            "COST": cost_rows,
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        # Both rows inserted (invalid price doesn't block the row)
        assert result["summary"]["COST"]["inserted"] == 2

        # But the bad price is flagged in rejected_rows
        rejected = result["rejected_rows"]
        price_issues = [r for r in rejected if r.get("reason") == "warn:invalid_number:unit_price"]
        assert len(price_issues) == 1
        assert price_issues[0]["tab"] == "COST"
        assert price_issues[0]["field"] == "unit_price"
        assert price_issues[0]["raw_value"] == "fifteen thousand"
        assert result["status"] == "partial"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_dry_run_writes_nothing(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        """dry_run=True must not save any DB documents or SheetSyncLog."""
        svc = _build_sheets_service({
            "DAILY_LOG": _daily_log_rows(),
            "ABW_SAMPLING": _abw_rows(),
            "COST": _cost_rows(),
            "HARVEST": _harvest_rows(),
            "MORTALITY": _mortality_rows(),
        })
        mock_get_svc.return_value = svc
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)

        result = SheetService.sync_cycle(CYCLE_ID, dry_run=True)

        # SheetSyncLog.save() must not be called in dry_run
        MockSyncLog.return_value.save.assert_not_called()

        # integration.save() must not be called
        integration.save.assert_not_called()

        # But summary should still reflect what would happen
        assert result["summary"]["DAILY_LOG"]["inserted"] == 3
        assert result["status"] == "ok"
        assert result["source_fingerprint"]

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_read_error_marks_tab_error_not_empty_success(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        svc = MagicMock()
        values = MagicMock()

        def get_side_effect(**kwargs):
            req = MagicMock()
            if kwargs["range"].startswith("COST"):
                resp = MagicMock()
                resp.status = 403
                req.execute.side_effect = HttpError(resp, b"forbidden")
            else:
                req.execute.return_value = {"values": []}
            return req

        values.get.side_effect = get_side_effect
        values.append.return_value.execute.return_value = {}
        svc.spreadsheets.return_value.values.return_value = values
        mock_get_svc.return_value = svc

        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        self._make_empty_db(MockCycleData, MockCostData, MockHarvest, MockFeed)
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert "error" in result["summary"]["COST"]
        assert result["status"] == "partial"
        sync_log_kwargs = MockSyncLog.call_args.kwargs
        assert sync_log_kwargs["spreadsheet_id"] == SPREADSHEET_ID
        assert sync_log_kwargs["source_fingerprint"] == result["source_fingerprint"]
        assert sync_log_kwargs["duration_seconds"] >= 0
        assert sync_log_kwargs["rows_per_second"] >= 0
        assert sync_log_kwargs["error_category"] == "google_auth"
        cost_summary = [
            ts for ts in sync_log_kwargs["tab_summaries"]
            if ts.tab == "COST"
        ][0]
        assert "forbidden" in cost_summary.error
        assert cost_summary.error_category == "google_auth"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_expected_fingerprint_mismatch_aborts_before_writes(
        self, mock_get_svc, MockCycle, MockIntegration, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [["2024-01-01", "1", "5.0"]],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        saved_log = MagicMock()
        saved_log.sync_id = UUID("12345678-1234-5678-1234-567812345678")
        MockSyncLog.return_value.save.return_value = saved_log

        result = SheetService.sync_cycle(CYCLE_ID, expected_fingerprint="stale")

        assert result["error"] == "Sheet changed since preview. Run preview-sync again."
        assert result["error_category"] == "stale_preview"
        assert integration.last_status == "error"
        assert integration.last_error_category == "stale_preview"
        assert integration.last_sync_log_id
        assert MockSyncLog.call_args.kwargs["error_category"] == "stale_preview"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_cost_existing_key_is_updated_not_skipped(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "HARVEST": [], "MORTALITY": [],
            "COST": [["2024-01-01", "Feed", "Starter feed", "200", "kg", "16000", "3200000", "PT Feed", "corrected"]],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        MockCycleData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        cost_doc = MagicMock()
        cost_doc.data = [{
            "date": "2024-01-01", "category": "Feed", "description": "Starter feed",
            "quantity": 100.0, "unit_price": 15000.0, "total": 1500000.0,
        }]
        MockCostData.objects.return_value.first.return_value = cost_doc
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["COST"]["updated"] == 1
        assert result["summary"]["COST"]["skipped"] == 0
        assert cost_doc.data[0]["quantity"] == 200.0
        assert cost_doc.data[0]["unit_price"] == 16000.0
        assert cost_doc.data[0]["notes"] == "corrected"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_cost_row_id_allows_description_correction(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "HARVEST": [], "MORTALITY": [],
            "COST": [["2024-01-01", "Feed", "Starter feed corrected", "100", "kg", "15000", "1500000", "PT Feed", "", "COST-3"]],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        MockCycleData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        cost_doc = MagicMock()
        cost_doc.data = [{
            "date": "2024-01-01",
            "sheet_row_id": "COST-3",
            "category": "Feed",
            "description": "Starter feed",
        }]
        MockCostData.objects.return_value.first.return_value = cost_doc
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["COST"]["updated"] == 1
        assert cost_doc.data[0]["description"] == "Starter feed corrected"

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_cost_delete_marker_removes_matching_row_id(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "HARVEST": [], "MORTALITY": [],
            "COST": [["2024-01-01", "Feed", "Starter feed", "", "", "", "", "", "", "COST-3", "Y"]],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        MockCycleData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        cost_doc = MagicMock()
        cost_doc.data = [
            {"date": "2024-01-01", "sheet_row_id": "COST-3", "category": "Feed", "description": "Starter feed"},
            {"date": "2024-01-02", "sheet_row_id": "COST-4", "category": "Feed", "description": "Grower feed"},
        ]
        MockCostData.objects.return_value.first.return_value = cost_doc
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["COST"]["deleted"] == 1
        assert [row["sheet_row_id"] for row in cost_doc.data] == ["COST-4"]
        cost_doc.save.assert_called_once()

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_mortality_existing_date_counts_as_update(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "COST": [], "HARVEST": [],
            "MORTALITY": [["2024-01-05", "5", "20", "corrected"]],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        cycle_data = MagicMock()
        cycle_data.result_data = [{"date": "2024-01-05", "mortality_count": 12}]
        MockCycleData.objects.return_value.first.return_value = cycle_data
        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["MORTALITY"]["inserted"] == 0
        assert result["summary"]["MORTALITY"]["updated"] == 1
        assert cycle_data.result_data[0]["mortality_count"] == 20

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_mortality_delete_marker_removes_matching_row_id(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [], "ABW_SAMPLING": [], "COST": [], "HARVEST": [],
            "MORTALITY": [["2024-01-05", "5", "", "", "MORTALITY-3", "Y"]],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        cycle_data = MagicMock()
        cycle_data.result_data = [
            {"date": "2024-01-05", "sheet_row_id": "MORTALITY-3", "mortality_count": 12},
            {"date": "2024-01-06", "sheet_row_id": "MORTALITY-4", "mortality_count": 8},
        ]
        MockCycleData.objects.return_value.first.return_value = cycle_data
        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        result = SheetService.sync_cycle(CYCLE_ID)

        assert result["summary"]["MORTALITY"]["deleted"] == 1
        assert [row["sheet_row_id"] for row in cycle_data.result_data] == ["MORTALITY-4"]
        cycle_data.save.assert_called()

    @patch("teramina.google_sheets.services.sheet_service.SheetSyncLog")
    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_existing_feed_realization_updates_feed_given_and_leftover(
        self, mock_get_svc, MockIntegration, MockCycle,
        MockCycleData, MockCostData, MockHarvest, MockFeed, MockSyncLog
    ):
        row = ["2024-01-01", "1", "5.0", "6.0", "", "28", "30", "",
               "7.5", "7.8", "15", "0.1", "35", "25", "2.5",
               "Starter", "40", "4", ""]
        mock_get_svc.return_value = _build_sheets_service({
            "DAILY_LOG": [row], "ABW_SAMPLING": [], "COST": [],
            "HARVEST": [], "MORTALITY": [],
        })
        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        cycle_data = MagicMock()
        cycle_data.result_data = [{"date": "2024-01-01", "doc": 1}]
        MockCycleData.objects.return_value.first.return_value = cycle_data
        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        existing_feed = MagicMock()
        existing_feed.doc = 1
        MockFeed.objects.return_value.only.return_value = [existing_feed]
        MockSyncLog.return_value.save.return_value = MockSyncLog.return_value

        SheetService.sync_cycle(CYCLE_ID)

        MockFeed.objects.return_value.update_one.assert_called_with(
            set__feed_given=25.0,
            set__feed_ration=25.0,
            set__last_updated=MockFeed.objects.return_value.update_one.call_args.kwargs["set__last_updated"],
            set__feed_leftover=2.5,
        )


# ── CreateTemplate tests ──────────────────────────────────────────────────

class TestCreateTemplate:
    @patch("teramina.google_sheets.services.sheet_service._share_spreadsheet")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service.Pond")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_create_template_success(self, mock_get_svc, MockCycle, MockPond,
                                     MockIntegration, mock_share):
        svc = _build_sheets_service({})
        mock_get_svc.return_value = svc

        cycle = MagicMock()
        cycle.id = CYCLE_ID
        cycle.name = "Cycle 1"
        cycle.start_date = START_DATE
        cycle.pond_id = "pond1"
        MockCycle.objects.return_value.first.return_value = cycle

        pond = MagicMock()
        pond.name = "Pond A"
        pond.size = 1000
        pond.depth = 1.5
        MockPond.objects.return_value.first.return_value = pond

        MockIntegration.objects.return_value.first.return_value = None
        MockIntegration.return_value = MagicMock()

        code, body = SheetService.create_template(
            CYCLE_ID, user_id=USER_ID, user_email="test@test.com"
        )
        assert code == 200
        assert body.payload["spreadsheet_id"] == SPREADSHEET_ID
        assert body.payload["auto_connected"] is True
        mock_share.assert_called_once()

    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    def test_create_template_no_cycle(self, MockCycle):
        MockCycle.objects.return_value.first.return_value = None
        code, body = SheetService.create_template(CYCLE_ID)
        assert code == 400


# ── Controller endpoint tests ─────────────────────────────────────────────

class TestSheetController:
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetSyncLog")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_sync_log_old_document_renders_without_new_fields(
        self, mock_user, mock_owner, MockSyncLog
    ):
        from teramina.google_sheets.controllers.sheet_controller import get_sync_log

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        old_tab_summary = SimpleNamespace(
            tab="DAILY_LOG",
            processed=1,
            inserted=1,
            updated=0,
            skipped=0,
            rejected=0,
        )
        old_log = SimpleNamespace(
            sync_id="12345678-1234-5678-1234-567812345678",
            cycle_id=CYCLE_ID,
            started_at=datetime(2024, 1, 1),
            finished_at=datetime(2024, 1, 1),
            status="ok",
            tab_summaries=[old_tab_summary],
            rejected_rows=[],
        )
        MockSyncLog.objects.return_value.first.return_value = old_log

        code, body = get_sync_log(MagicMock(), CYCLE_ID)

        assert code == 200
        assert body.payload["spreadsheet_id"] is None
        assert body.payload["source_fingerprint"] is None
        assert body.payload["duration_seconds"] is None
        assert body.payload["rows_per_second"] is None
        assert body.payload["error_category"] is None
        assert body.payload["tab_summaries"][0]["deleted"] == 0
        assert body.payload["tab_summaries"][0]["error"] is None
        assert body.payload["tab_summaries"][0]["error_category"] is None

    @patch("teramina.google_sheets.controllers.sheet_controller.SheetSyncLog")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_sync_log_can_filter_by_sync_id(self, mock_user, mock_owner, MockSyncLog):
        from teramina.google_sheets.controllers.sheet_controller import get_sync_log

        sync_id = "12345678-1234-5678-1234-567812345678"
        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        log = SimpleNamespace(
            sync_id=sync_id,
            cycle_id=CYCLE_ID,
            spreadsheet_id=SPREADSHEET_ID,
            source_fingerprint="fingerprint-1",
            started_at=datetime(2024, 1, 1),
            finished_at=datetime(2024, 1, 1),
            duration_seconds=2.0,
            rows_per_second=4.5,
            status="error",
            error_category="google_auth",
            tab_summaries=[
                SimpleNamespace(
                    tab="COST",
                    processed=0,
                    inserted=0,
                    updated=0,
                    deleted=0,
                    skipped=0,
                    rejected=0,
                    error="forbidden",
                    error_category="google_auth",
                )
            ],
            rejected_rows=[],
        )
        MockSyncLog.objects.return_value.first.return_value = log

        code, body = get_sync_log(MagicMock(), CYCLE_ID, sync_id)

        assert code == 200
        MockSyncLog.objects.assert_called_once_with(cycle_id=CYCLE_ID, sync_id=UUID(sync_id))
        assert body.payload["sync_id"] == sync_id
        assert body.payload["rows_per_second"] == 4.5
        assert body.payload["error_category"] == "google_auth"

    @patch("teramina.google_sheets.controllers.sheet_controller.sync_single_cycle")
    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_manual_sync_returns_queued_sync_id(
        self, mock_user, mock_owner, MockIntegration, mock_cache, mock_task
    ):
        from teramina.google_sheets.controllers.sheet_controller import manual_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        mock_cache.get.return_value = None
        integration = MagicMock()
        MockIntegration.objects.return_value.first.return_value = integration

        code, body = manual_sync(MagicMock(), CYCLE_ID)

        assert code == 200
        assert body.payload["cycle_id"] == CYCLE_ID
        assert body.payload["status"] == "queued"
        assert body.payload["sync_id"]
        assert integration.last_status == "queued"
        assert str(integration.active_sync_id) == body.payload["sync_id"]
        mock_task.delay.assert_called_once_with(
            CYCLE_ID,
            None,
            body.payload["sync_id"],
            "valid_rows_only",
        )

    @patch("teramina.google_sheets.controllers.sheet_controller.sync_single_cycle")
    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_manual_sync_lock_contention_returns_400(
        self, mock_user, mock_owner, MockIntegration, mock_cache, mock_task
    ):
        from teramina.google_sheets.controllers.sheet_controller import manual_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        mock_cache.get.return_value = "1"
        MockIntegration.objects.return_value.first.return_value = MagicMock()

        code, body = manual_sync(MagicMock(), CYCLE_ID)

        assert code == 400
        assert body.message == "Sync already in progress"
        mock_task.delay.assert_not_called()

    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetService")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_preview_sync_stores_source_fingerprint(
        self, mock_user, mock_owner, MockService, MockIntegration, mock_cache
    ):
        from teramina.google_sheets.controllers.sheet_controller import preview_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        MockIntegration.objects.return_value.first.return_value = MagicMock()
        MockService.sync_cycle.return_value = {
            "summary": {"DAILY_LOG": {"inserted": 1, "updated": 0, "skipped": 0, "rejected": 0}},
            "rejected_rows": [],
            "source_fingerprint": "fingerprint-1",
            "status": "ok",
        }

        code, body = preview_sync(MagicMock(), CYCLE_ID)

        assert code == 200
        assert body.payload["preview_id"]
        cache_payload = mock_cache.set.call_args.args[1]
        assert cache_payload["cycle_id"] == CYCLE_ID
        assert cache_payload["source_fingerprint"] == "fingerprint-1"

    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetService")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_preview_sync_strict_blocks_errors(
        self, mock_user, mock_owner, MockService, MockIntegration, mock_cache
    ):
        from teramina.google_sheets.controllers.sheet_controller import preview_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        MockIntegration.objects.return_value.first.return_value = MagicMock()
        MockService.sync_cycle.return_value = {
            "summary": {"DAILY_LOG": {"inserted": 0, "updated": 0, "skipped": 0, "rejected": 1}},
            "rejected_rows": [{"reason": "invalid_date"}],
            "source_fingerprint": "fingerprint-1",
            "status": "partial",
        }

        code, body = preview_sync(MagicMock(), CYCLE_ID, import_mode="strict")

        assert code == 400
        assert body.message == "Strict import blocked because the sheet has errors."
        mock_cache.set.assert_not_called()

    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetService")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_preview_sync_strict_allows_warning_only_rows(
        self, mock_user, mock_owner, MockService, MockIntegration, mock_cache
    ):
        from teramina.google_sheets.controllers.sheet_controller import preview_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        MockIntegration.objects.return_value.first.return_value = MagicMock()
        MockService.sync_cycle.return_value = {
            "summary": {"DAILY_LOG": {"inserted": 1, "updated": 0, "skipped": 0, "rejected": 1}},
            "rejected_rows": [
                {
                    "tab": "DAILY_LOG",
                    "row_number": 3,
                    "field": "do_morning",
                    "raw_value": "3.9",
                    "reason": "warn:low_do",
                }
            ],
            "source_fingerprint": "fingerprint-1",
            "status": "partial",
        }

        code, body = preview_sync(MagicMock(), CYCLE_ID, import_mode="strict")

        assert code == 200
        assert body.payload["rows_warning"] == 1
        assert body.payload["rows_error"] == 0
        mock_cache.set.assert_called_once()

    @patch("teramina.google_sheets.controllers.sheet_controller.sync_single_cycle")
    @patch("teramina.google_sheets.controllers.sheet_controller.cache")
    @patch("teramina.google_sheets.controllers.sheet_controller.SheetIntegration")
    @patch("teramina.google_sheets.controllers.sheet_controller.verify_cycle_owner")
    @patch("teramina.google_sheets.controllers.sheet_controller.get_signed_in_user")
    def test_confirm_sync_passes_preview_fingerprint_to_task(
        self, mock_user, mock_owner, MockIntegration, mock_cache, mock_task
    ):
        from teramina.google_sheets.controllers.sheet_controller import confirm_sync

        mock_user.return_value = SimpleNamespace(id=USER_ID)
        mock_owner.return_value = True
        mock_cache.get.side_effect = [
            {"cycle_id": CYCLE_ID, "source_fingerprint": "fingerprint-1"},
            None,
        ]
        integration = MagicMock()
        MockIntegration.objects.return_value.first.return_value = integration

        code, body = confirm_sync(MagicMock(), "preview-1")

        assert code == 200
        assert body.payload["preview_id"] == "preview-1"
        assert body.payload["status"] == "queued"
        assert body.payload["sync_id"]
        assert integration.last_status == "queued"
        mock_cache.delete.assert_called_once_with("sheet_preview:preview-1")
        mock_task.delay.assert_called_once_with(
            CYCLE_ID,
            "fingerprint-1",
            body.payload["sync_id"],
            "valid_rows_only",
        )


# ── Celery task tests ─────────────────────────────────────────────────────

class TestSyncTasks:
    @patch("teramina.google_sheets.tasks.sync_tasks.cache")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetService")
    def test_sync_single(self, MockService, mock_cache):
        mock_cache.add.return_value = True
        MockService.sync_cycle.return_value = {
            "summary": {"DAILY_LOG": {"inserted": 1}},
            "status": "ok",
        }
        from teramina.google_sheets.tasks.sync_tasks import sync_single_cycle
        result = sync_single_cycle(CYCLE_ID)
        MockService.sync_cycle.assert_called_once_with(
            CYCLE_ID,
            expected_fingerprint=None,
            sync_id=None,
        )
        mock_cache.delete.assert_called_once()
        assert "summary" in result

    @patch("teramina.google_sheets.tasks.sync_tasks.cache")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetService")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetIntegration")
    def test_sync_all(self, MockIntegration, MockService, mock_cache):
        mock_cache.add.return_value = True
        i1 = MagicMock()
        i1.cycle_id = "c1"
        i2 = MagicMock()
        i2.cycle_id = "c2"
        MockIntegration.objects.return_value.only.return_value = [i1, i2]
        MockService.sync_cycle.return_value = {}

        from teramina.google_sheets.tasks.sync_tasks import sync_all_active_sheets
        result = sync_all_active_sheets()
        assert result["synced"] == 2
        assert result["errors"] == 0

    @patch("teramina.google_sheets.tasks.sync_tasks.cache")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetIntegration")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetService")
    def test_strict_sync_blocks_before_write(self, MockService, MockIntegration, mock_cache):
        mock_cache.add.return_value = True
        integration = MagicMock()
        MockIntegration.objects.return_value.first.return_value = integration
        MockService.sync_cycle.return_value = {
            "summary": {"DAILY_LOG": {"inserted": 0, "updated": 0, "skipped": 0, "rejected": 1}},
            "rejected_rows": [{"reason": "invalid_date"}],
            "source_fingerprint": "fingerprint-1",
        }

        from teramina.google_sheets.tasks.sync_tasks import sync_single_cycle
        result = sync_single_cycle(CYCLE_ID, import_mode="strict")

        assert result["error"] == "Strict import blocked because the sheet has errors."
        assert result["error_category"] == "validation"
        assert MockService.sync_cycle.call_count == 1
        assert MockService.sync_cycle.call_args.kwargs["dry_run"] is True
        assert integration.last_status == "error"
        assert integration.last_error_category == "validation"
        mock_cache.delete.assert_called_once()

    @patch("teramina.google_sheets.tasks.sync_tasks.cache")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetIntegration")
    def test_lock_contention_marks_error_category(self, MockIntegration, mock_cache):
        mock_cache.add.return_value = False
        integration = MagicMock()
        MockIntegration.objects.return_value.first.return_value = integration

        from teramina.google_sheets.tasks.sync_tasks import sync_single_cycle
        result = sync_single_cycle(CYCLE_ID, sync_id="12345678-1234-5678-1234-567812345678")

        assert result["error"] == "Sync already in progress"
        assert result["error_category"] == "lock_contention"
        assert integration.last_status == "error"
        assert integration.last_error_category == "lock_contention"
        mock_cache.delete.assert_not_called()
