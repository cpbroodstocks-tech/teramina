"""E2E tests for the Google Sheets integration (service layer)."""
import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError

from tests.conftest import (
    CYCLE_ID, USER_ID, SPREADSHEET_ID, SPREADSHEET_URL, START_DATE,
    _build_sheets_service, _build_drive_service,
    _daily_log_rows, _abw_rows, _cost_rows, _harvest_rows, _mortality_rows,
)

from teramina.google_sheets.services.sheet_service import (
    SheetService, _normalize_date, _safe_float, _safe_int, _safe_str,
    _auto_fill_doc, _col, _upsert_result_data,
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

    def test_preserves_unparseable(self):
        result = _normalize_date("not-a-date")
        assert result == "not-a-date"


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

    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    def test_status_active(self, MockIntegration):
        integration = MagicMock()
        integration.spreadsheet_id = SPREADSHEET_ID
        integration.spreadsheet_url = SPREADSHEET_URL
        integration.is_active = True
        integration.last_synced = datetime(2024, 1, 15)
        integration.last_status = "ok"
        integration.last_error = ""
        integration.rows_synced = 42
        MockIntegration.objects.return_value.first.return_value = integration

        code, body = SheetService.get_status(CYCLE_ID)
        assert code == 200
        assert body.payload["is_active"] is True
        assert body.payload["rows_synced"] == 42


# ── SyncCycle tests ───────────────────────────────────────────────────────

class TestSyncCycle:
    def _make_integration(self):
        i = MagicMock()
        i.spreadsheet_id = SPREADSHEET_ID
        i.is_active = True
        i.last_status = "pending"
        i.rows_synced = 0
        return i

    def _make_cycle(self):
        c = MagicMock()
        c.id = CYCLE_ID
        c.start_date = START_DATE
        c.pond_id = "pond1"
        return c

    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_full_sync(self, mock_get_svc, MockIntegration, MockCycle,
                       MockCycleData, MockCostData, MockHarvest, MockFeed):
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

        cycle = self._make_cycle()
        MockCycle.objects.return_value.first.return_value = cycle

        # Empty existing data
        MockCycleData.objects.return_value.first.return_value = None
        cd_new = MagicMock()
        cd_new.result_data = []
        cd_new.save.return_value = cd_new
        MockCycleData.return_value = cd_new

        MockCostData.objects.return_value.first.return_value = None
        MockCostData.return_value = MagicMock()

        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []

        summary = SheetService.sync_cycle(CYCLE_ID)

        assert "DAILY_LOG" in summary
        assert summary["DAILY_LOG"]["inserted"] == 3
        assert summary["DAILY_LOG"]["rejected"] == 0
        assert "ABW_SAMPLING" in summary
        assert summary["ABW_SAMPLING"]["inserted"] == 2
        assert "COST" in summary
        assert summary["COST"]["inserted"] == 2
        assert "HARVEST" in summary
        assert summary["HARVEST"]["inserted"] == 2
        assert "MORTALITY" in summary
        assert summary["MORTALITY"]["inserted"] == 2
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

    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_date_normalization(self, mock_get_svc, MockIntegration,
                                     MockCycle, MockCycleData, MockCostData,
                                     MockHarvest, MockFeed):
        """DD/MM/YYYY format should be normalized."""
        svc = _build_sheets_service({
            "DAILY_LOG": [["15/01/2024", "", "5.0", "6.0"]],
            "ABW_SAMPLING": [], "COST": [], "HARVEST": [], "MORTALITY": [],
        })
        mock_get_svc.return_value = svc

        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()

        cd = MagicMock()
        cd.result_data = []
        cd.save.return_value = cd
        MockCycleData.objects.return_value.first.return_value = None
        MockCycleData.return_value = cd

        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []

        summary = SheetService.sync_cycle(CYCLE_ID)
        assert summary["DAILY_LOG"]["inserted"] == 1
        assert summary["DAILY_LOG"]["rejected"] == 0

    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_auto_doc_computation(self, mock_get_svc, MockIntegration,
                                       MockCycle, MockCycleData, MockCostData,
                                       MockHarvest, MockFeed):
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
        cd = MagicMock()
        cd.result_data = []
        cd.save.return_value = cd
        MockCycleData.objects.return_value.first.return_value = None

        def capture_init(**kwargs):
            saved_rows.append(kwargs.get("result_data", []))
            m = MagicMock()
            m.result_data = kwargs.get("result_data", [])
            m.save.return_value = m
            return m
        MockCycleData.side_effect = capture_init

        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []

        SheetService.sync_cycle(CYCLE_ID)
        assert len(saved_rows) > 0
        assert saved_rows[0][0]["doc"] == 10  # Jan 10 - Jan 1 + 1

    @patch("teramina.google_sheets.services.sheet_service.FeedRealization")
    @patch("teramina.google_sheets.services.sheet_service.HarvestRecord")
    @patch("teramina.google_sheets.services.sheet_service.CostData")
    @patch("teramina.google_sheets.services.sheet_service.CycleData")
    @patch("teramina.google_sheets.services.sheet_service.Cycle")
    @patch("teramina.google_sheets.services.sheet_service.SheetIntegration")
    @patch("teramina.google_sheets.services.sheet_service._get_sheets_service")
    def test_sync_empty_sheet(self, mock_get_svc, MockIntegration, MockCycle,
                              MockCycleData, MockCostData, MockHarvest, MockFeed):
        """Empty sheet should result in zero rows and status ok."""
        svc = _build_sheets_service({})
        mock_get_svc.return_value = svc

        integration = self._make_integration()
        MockIntegration.objects.return_value.first.return_value = integration
        MockCycle.objects.return_value.first.return_value = self._make_cycle()
        MockCycleData.objects.return_value.first.return_value = None
        MockCostData.objects.return_value.first.return_value = None
        MockHarvest.objects.return_value = []
        MockFeed.objects.return_value.only.return_value = []

        summary = SheetService.sync_cycle(CYCLE_ID)
        for tab in ["DAILY_LOG", "ABW_SAMPLING", "COST", "HARVEST", "MORTALITY"]:
            assert tab in summary
            assert summary[tab].get("rejected", 0) == 0


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


# ── Celery task tests ─────────────────────────────────────────────────────

class TestSyncTasks:
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetService")
    def test_sync_single(self, MockService):
        MockService.sync_cycle.return_value = {"DAILY_LOG": {"inserted": 1}}
        from teramina.google_sheets.tasks.sync_tasks import sync_single_cycle
        result = sync_single_cycle(CYCLE_ID)
        MockService.sync_cycle.assert_called_once_with(CYCLE_ID)
        assert "DAILY_LOG" in result

    @patch("teramina.google_sheets.tasks.sync_tasks.SheetService")
    @patch("teramina.google_sheets.tasks.sync_tasks.SheetIntegration")
    def test_sync_all(self, MockIntegration, MockService):
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
