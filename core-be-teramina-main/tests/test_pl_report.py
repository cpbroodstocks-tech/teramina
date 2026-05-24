# pylint: disable=redefined-outer-name
"""
Tests for the P&L report layer.

Covers:
  ProfitLossService
    - missing cycle / missing data guards
    - _compute_costs: cum_total_cost path vs. column-sum fallback
    - _projected_remaining: inactive returns None; active returns potential_revenue
    - _build_harvest_events: skips empty slots; sorts and numbers events
    - _build_kpi: SR normalisation (fraction → pct)
    - _doc_bucket / _density_bucket: all boundary values

  Route alias (GET /cycles/{cycle_id}/report/pl)
    - 401 when ownership check fails
    - 200 + correct payload when all checks pass

  Aggregate failure behaviour
    - FarmProfitLossService: any cycle failure → ValueError naming the cycle
    - FarmProfitLossService: zero cycles → ValueError
    - YearProfitLossService: any ProfitLossService failure → ValueError naming the cycle
    - YearProfitLossService: no overlapping data → ValueError
    - YearProfitLossService: cycles outside year boundary are silently skipped (not failures)
"""

import pytest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

# conftest.py handles Django setup and heavy-dep stubs


# ─── helpers ──────────────────────────────────────────────────────────────────

def _result_rows(n=80, *, is_active=False):
    """Minimal ResultData rows for an n-day historical cycle."""
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "doc": i,
            "category": "historical",
            "adj_abw": 5.0 + i * 0.3,
            "sr": 0.85,
            "fcr": 1.5,
            "total_biomass": 1_000.0 + i * 10,
            "cum_total_cost": 10_000_000.0 + i * 100_000,
            "cost_feed": 5_000.0,
            "cost_labor": 1_000.0,
            "cost_energy": 500.0,
            "cost_probiotics": 200.0,
            "cost_bonuss": 100.0,
            "cost_harvest": 300.0,
            "cost_other": 50.0,
            "cost_seed": 0.0,
            "potential_revenue": 8_000_000.0 if is_active else 0.0,
            "initial_stocking": 50_000.0,
        })
    return rows


def _make_cycle_report(**overrides):
    """Minimal valid dict that ProfitLossService.get_report() returns."""
    base = {
        "cycle_id": "cycle_001",
        "cycle_name": "Cycle A",
        "pond_id": "pond_001",
        "pond_name": "Pond A",
        "start_date": "2024-01-01",
        "generated_at": datetime.now().isoformat(),
        "is_active": True,
        "doc_range": "DOC 1–80",
        "currency": "IDR",
        "harvest_events": [],
        "realized_revenue_idr": 50_000_000,
        "projected_remaining_idr": 5_000_000,
        "total_revenue_idr": 55_000_000,
        "cost_seed_idr": 0,
        "cost_feed_idr": 10_000_000,
        "cost_harvest_idr": 500_000,
        "total_cogs_idr": 10_500_000,
        "gross_profit_idr": 44_500_000,
        "gross_margin_pct": 80.9,
        "cost_labor_idr": 3_000_000,
        "cost_energy_idr": 1_000_000,
        "cost_probiotics_idr": 500_000,
        "cost_bonus_idr": 200_000,
        "cost_other_idr": 100_000,
        "total_opex_idr": 4_800_000,
        "total_cost_idr": 15_300_000,
        "net_profit_idr": 39_700_000,
        "net_margin_pct": 72.2,
        "kpi": {
            "doc": 80,
            "total_harvest_kg": 800.0,
            "final_abw_g": 22.0,
            "survival_rate_pct": 85.0,
            "fcr": 1.5,
            "cost_per_kg_idr": 19_125,
            "revenue_per_kg_idr": 68_750,
            "break_even_price_idr": 19_125,
        },
        "benchmark": [],
        "benchmark_available": False,
    }
    base.update(overrides)
    return base


# ─── ProfitLossService ────────────────────────────────────────────────────────

class TestProfitLossServiceGuards:
    """Missing-data guards that must raise ValueError."""

    def _patches(self):
        return (
            patch("teramina.pl_report.services.pl_report_service.Cycle"),
            patch("teramina.pl_report.services.pl_report_service.Pond"),
            patch("teramina.pl_report.services.pl_report_service.ResultData"),
            patch("teramina.pl_report.services.pl_report_service.HarvestRecord"),
            patch("teramina.pl_report.services.pl_report_service.BenchmarkCohort"),
        )

    def test_cycle_not_found_raises(self):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        with (
            patch("teramina.pl_report.services.pl_report_service.Cycle") as MC,
            patch("teramina.pl_report.services.pl_report_service.Pond"),
            patch("teramina.pl_report.services.pl_report_service.ResultData"),
            patch("teramina.pl_report.services.pl_report_service.HarvestRecord"),
            patch("teramina.pl_report.services.pl_report_service.BenchmarkCohort"),
        ):
            MC.objects.return_value.first.return_value = None
            with pytest.raises(ValueError, match="not found"):
                ProfitLossService("missing_id").get_report()

    def test_no_result_data_raises(self):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        fake_cycle = SimpleNamespace(id="c1", name="C1", pond_id="p1", is_active=False, start_date=None)
        fake_pond = SimpleNamespace(id="p1", name="Pond A", size=1000)
        with (
            patch("teramina.pl_report.services.pl_report_service.Cycle") as MC,
            patch("teramina.pl_report.services.pl_report_service.Pond") as MP,
            patch("teramina.pl_report.services.pl_report_service.ResultData") as MR,
            patch("teramina.pl_report.services.pl_report_service.HarvestRecord"),
            patch("teramina.pl_report.services.pl_report_service.BenchmarkCohort"),
        ):
            MC.objects.return_value.first.return_value = fake_cycle
            MP.objects.return_value.first.return_value = fake_pond
            MR.objects.return_value.only.return_value.first.return_value = None
            with pytest.raises(ValueError, match="No result data"):
                ProfitLossService("c1").get_report()

    def test_empty_historical_rows_raises(self):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        fake_cycle = SimpleNamespace(id="c1", name="C1", pond_id="p1", is_active=False, start_date=None)
        fake_pond = SimpleNamespace(id="p1", name="Pond A", size=1000)
        fake_rd = SimpleNamespace(result_data=[{"doc": 1, "category": "forecast"}])
        with (
            patch("teramina.pl_report.services.pl_report_service.Cycle") as MC,
            patch("teramina.pl_report.services.pl_report_service.Pond") as MP,
            patch("teramina.pl_report.services.pl_report_service.ResultData") as MR,
            patch("teramina.pl_report.services.pl_report_service.HarvestRecord"),
            patch("teramina.pl_report.services.pl_report_service.BenchmarkCohort"),
        ):
            MC.objects.return_value.first.return_value = fake_cycle
            MP.objects.return_value.first.return_value = fake_pond
            MR.objects.return_value.only.return_value.first.return_value = fake_rd
            with pytest.raises(ValueError, match="No historical"):
                ProfitLossService("c1").get_report()


class TestProfitLossServiceFullReport:
    """Happy-path and financial calculation tests."""

    def _run(self, rows, harvest_data=None, is_active=False, pond_size=1000):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        fake_cycle = SimpleNamespace(
            id="c1", name="Test Cycle", pond_id="p1",
            is_active=is_active, start_date=datetime(2024, 1, 1)
        )
        fake_pond = SimpleNamespace(id="p1", name="Pond A", size=pond_size)
        fake_rd = SimpleNamespace(result_data=rows)
        fake_hr = MagicMock()
        fake_hr.harvest_data = harvest_data or {}

        with (
            patch("teramina.pl_report.services.pl_report_service.Cycle") as MC,
            patch("teramina.pl_report.services.pl_report_service.Pond") as MP,
            patch("teramina.pl_report.services.pl_report_service.ResultData") as MR,
            patch("teramina.pl_report.services.pl_report_service.HarvestRecord") as MH,
            patch("teramina.pl_report.services.pl_report_service.BenchmarkCohort") as MB,
        ):
            MC.objects.return_value.first.return_value = fake_cycle
            MP.objects.return_value.first.return_value = fake_pond
            MR.objects.return_value.only.return_value.first.return_value = fake_rd
            MH.objects.return_value.first.return_value = fake_hr
            MB.objects.return_value.first.return_value = None
            return ProfitLossService("c1").get_report()

    def test_report_has_required_keys(self):
        report = self._run(_result_rows())
        required = [
            "cycle_id", "cycle_name", "total_revenue_idr", "total_cogs_idr",
            "total_opex_idr", "total_cost_idr", "net_profit_idr", "net_margin_pct",
            "gross_profit_idr", "gross_margin_pct", "kpi", "harvest_events",
            "benchmark", "benchmark_available",
        ]
        for key in required:
            assert key in report, f"Missing key: {key}"

    def test_costs_use_cum_total_cost_column(self):
        """When cum_total_cost is present, total_cost_idr equals its last value."""
        rows = _result_rows(10)
        report = self._run(rows)
        expected = int(rows[-1]["cum_total_cost"])
        assert report["total_cost_idr"] == expected

    def test_costs_fallback_to_column_sum(self):
        """When cum_total_cost is absent, total is sum of individual columns + seed."""
        rows = []
        for i in range(1, 6):
            rows.append({
                "doc": i,
                "category": "historical",
                "adj_abw": 10.0,
                "sr": 0.85,
                "fcr": 1.5,
                "total_biomass": 500.0,
                "cost_feed": 1_000.0,
                "cost_labor": 500.0,
                "cost_energy": 200.0,
                "cost_probiotics": 100.0,
                "cost_bonuss": 50.0,
                "cost_harvest": 150.0,
                "cost_other": 25.0,
                "cost_seed": 10.0,
                "initial_stocking": 50_000.0,
            })
        report = self._run(rows)
        expected_per_row = 1_000 + 500 + 200 + 100 + 50 + 150 + 25 + 10
        assert report["total_cost_idr"] == expected_per_row * 5

    def test_inactive_cycle_has_no_projected_remaining(self):
        report = self._run(_result_rows(80, is_active=False), is_active=False)
        assert report["projected_remaining_idr"] is None

    def test_active_cycle_includes_projected_remaining(self):
        report = self._run(_result_rows(80, is_active=True), is_active=True)
        assert report["projected_remaining_idr"] == 8_000_000

    def test_sr_fraction_normalised_to_percent(self):
        """sr=0.85 in the data must appear as 85.0 in KPI."""
        report = self._run(_result_rows(80))
        assert report["kpi"]["survival_rate_pct"] == pytest.approx(85.0, abs=0.1)

    def test_harvest_events_sorted_and_numbered(self):
        harvest = {
            "final":    {"doc": 80, "biomass": 700.0, "revenue": 50_400_000},
            "partial1": {"doc": 60, "biomass": 300.0, "revenue": 19_500_000},
        }
        report = self._run(_result_rows(80), harvest_data=harvest)
        events = report["harvest_events"]
        assert len(events) == 2
        assert events[0]["doc"] == 60
        assert events[0]["harvest_no"] == 1
        assert events[1]["doc"] == 80
        assert events[1]["harvest_no"] == 2

    def test_harvest_events_skips_empty_slots(self):
        harvest = {
            "partial1": {"doc": "", "biomass": "", "revenue": ""},
            "final":    {"doc": 80, "biomass": 700.0, "revenue": 50_400_000},
        }
        report = self._run(_result_rows(80), harvest_data=harvest)
        assert len(report["harvest_events"]) == 1
        assert report["harvest_events"][0]["doc"] == 80

    def test_revenue_is_sum_of_harvest_events(self):
        harvest = {
            "partial1": {"doc": 60, "biomass": 300.0, "revenue": 19_500_000},
            "final":    {"doc": 80, "biomass": 700.0, "revenue": 50_400_000},
        }
        report = self._run(_result_rows(80), is_active=False, harvest_data=harvest)
        # inactive → no projected; revenue = sum of events
        assert report["total_revenue_idr"] == 19_500_000 + 50_400_000

    def test_net_profit_equals_revenue_minus_total_cost(self):
        report = self._run(_result_rows(80))
        assert report["net_profit_idr"] == report["total_revenue_idr"] - report["total_cost_idr"]

    def test_gross_profit_equals_revenue_minus_cogs(self):
        report = self._run(_result_rows(80))
        assert report["gross_profit_idr"] == report["total_revenue_idr"] - report["total_cogs_idr"]


class TestDocBucket:
    def _b(self, doc):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        return ProfitLossService._doc_bucket(doc)

    def test_boundary_60(self):   assert self._b(60) == "1-60"
    def test_boundary_61(self):   assert self._b(61) == "61-90"
    def test_boundary_90(self):   assert self._b(90) == "61-90"
    def test_boundary_91(self):   assert self._b(91) == "91-120"
    def test_boundary_120(self):  assert self._b(120) == "91-120"
    def test_boundary_121(self):  assert self._b(121) == "121+"
    def test_boundary_200(self):  assert self._b(200) == "121+"


class TestDensityBucket:
    def _b(self, density):
        from teramina.pl_report.services.pl_report_service import ProfitLossService
        return ProfitLossService._density_bucket(density)

    def test_below_50(self):      assert self._b(49.9) == "<50"
    def test_at_50(self):         assert self._b(50) == "50-100"
    def test_at_100(self):        assert self._b(100) == "50-100"
    def test_at_101(self):        assert self._b(101) == "100-200"
    def test_at_200(self):        assert self._b(200) == "100-200"
    def test_above_200(self):     assert self._b(201) == ">200"


# ─── Route alias controller ───────────────────────────────────────────────────

class TestPLReportAliasController:
    """Tests for GET /cycles/{cycle_id}/report/pl."""

    def _call(self, cycle_id="cycle_abc", *, owner=True, report=None):
        from teramina.pl_report.controllers.pl_report_alias_controller import get_pl_report_by_path
        fake_request = MagicMock()
        with (
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.get_signed_in_user",
                return_value=SimpleNamespace(id="user_001"),
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.verify_cycle_owner",
                return_value=owner,
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.ProfitLossService",
            ) as MockSvc,
        ):
            MockSvc.return_value.get_report.return_value = report or _make_cycle_report()
            return get_pl_report_by_path(fake_request, cycle_id)

    def test_non_owner_returns_401(self):
        status, resp = self._call(owner=False)
        assert status == 401

    def test_owner_returns_200(self):
        status, resp = self._call(owner=True)
        assert status == 200

    def test_payload_matches_service_output(self):
        expected = _make_cycle_report(cycle_id="cycle_abc", net_profit_idr=99_000_000)
        status, resp = self._call(report=expected)
        assert resp.payload == expected

    def test_service_called_with_correct_cycle_id(self):
        from teramina.pl_report.controllers.pl_report_alias_controller import get_pl_report_by_path
        fake_request = MagicMock()
        with (
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.get_signed_in_user",
                return_value=SimpleNamespace(id="user_001"),
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.verify_cycle_owner",
                return_value=True,
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.ProfitLossService",
            ) as MockSvc,
        ):
            MockSvc.return_value.get_report.return_value = _make_cycle_report()
            get_pl_report_by_path(fake_request, "specific_id_xyz")
            MockSvc.assert_called_once_with("specific_id_xyz")

    def test_service_value_error_returns_400(self):
        from teramina.pl_report.controllers.pl_report_alias_controller import get_pl_report_by_path
        fake_request = MagicMock()
        with (
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.get_signed_in_user",
                return_value=SimpleNamespace(id="user_001"),
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.verify_cycle_owner",
                return_value=True,
            ),
            patch(
                "teramina.pl_report.controllers.pl_report_alias_controller.ProfitLossService",
            ) as MockSvc,
        ):
            MockSvc.return_value.get_report.side_effect = ValueError("cycle gone")
            status, resp = get_pl_report_by_path(fake_request, "bad_id")
        assert status == 400
        assert "cycle gone" in resp.message


# ─── FarmProfitLossService aggregate failures ─────────────────────────────────

class TestFarmAggregateFailureBehaviour:

    def _setup_patches(self, ponds, cycles_per_pond, pl_side_effects):
        """
        ponds: list of SimpleNamespace(id, name)
        cycles_per_pond: dict pond_id → list of SimpleNamespace(id, name)
        pl_side_effects: dict cycle_id → return_value or Exception instance
        """
        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService

        fake_farm = SimpleNamespace(id="farm_001", name="Test Farm", location="Jakarta")

        def mock_pl_factory(cycle_id):
            mock = MagicMock()
            effect = pl_side_effects.get(cycle_id)
            if isinstance(effect, Exception):
                mock.get_report.side_effect = effect
            else:
                mock.get_report.return_value = effect or _make_cycle_report(cycle_id=cycle_id)
            return mock

        svc = FarmProfitLossService("farm_001")

        with (
            patch("teramina.pl_report.services.farm_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.farm_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.farm_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.farm_pl_service.ProfitLossService", side_effect=mock_pl_factory),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = ponds

            def cycle_query(pond_id, is_active):
                mock_qs = MagicMock()
                mock_qs.only.return_value = cycles_per_pond.get(pond_id, [])
                return mock_qs

            MC.objects.side_effect = lambda pond_id, is_active: cycle_query(pond_id, is_active)

            return svc.get_report()

    def _make_pond(self, pid, name):
        return SimpleNamespace(id=pid, name=name)

    def _make_cycle(self, cid, name):
        return SimpleNamespace(id=cid, name=name)

    def test_farm_not_found_raises(self):
        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService
        svc = FarmProfitLossService("ghost_farm")
        with patch("teramina.pl_report.services.farm_pl_service.Farm") as MF:
            MF.objects.return_value.first.return_value = None
            with pytest.raises(ValueError, match="not found"):
                svc.get_report()

    def test_no_ponds_raises(self):
        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService
        fake_farm = SimpleNamespace(id="f1", name="F", location="")
        svc = FarmProfitLossService("f1")
        with (
            patch("teramina.pl_report.services.farm_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.farm_pl_service.Pond") as MP,
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = []
            with pytest.raises(ValueError, match="No ponds"):
                svc.get_report()

    def test_one_cycle_fails_raises_with_cycle_name(self):
        pond = self._make_pond("p1", "Pond Alpha")
        cycle_ok = self._make_cycle("c_ok", "Cycle Good")
        cycle_bad = self._make_cycle("c_bad", "Cycle Broken")

        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService
        fake_farm = SimpleNamespace(id="farm_001", name="Test Farm", location="")

        def mock_pl_factory(cycle_id):
            mock = MagicMock()
            if cycle_id == "c_bad":
                mock.get_report.side_effect = RuntimeError("DB timeout")
            else:
                mock.get_report.return_value = _make_cycle_report(cycle_id=cycle_id)
            return mock

        svc = FarmProfitLossService("farm_001")
        with (
            patch("teramina.pl_report.services.farm_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.farm_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.farm_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.farm_pl_service.ProfitLossService", side_effect=mock_pl_factory),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [pond]
            MC.objects.return_value.only.return_value = [cycle_ok, cycle_bad]

            with pytest.raises(ValueError) as exc_info:
                svc.get_report()

        msg = str(exc_info.value)
        assert "Cycle Broken" in msg, f"Expected 'Cycle Broken' in error: {msg}"
        assert "DB timeout" in msg

    def test_all_cycles_succeed_returns_aggregate(self):
        pond = self._make_pond("p1", "Pond Alpha")
        cycle = self._make_cycle("c_ok", "Cycle Good")
        report = _make_cycle_report(cycle_id="c_ok", total_revenue_idr=55_000_000)

        fake_farm = SimpleNamespace(id="farm_001", name="Test Farm", location="")

        def mock_pl_factory(cycle_id):
            mock = MagicMock()
            mock.get_report.return_value = report
            return mock

        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService
        svc = FarmProfitLossService("farm_001")

        with (
            patch("teramina.pl_report.services.farm_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.farm_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.farm_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.farm_pl_service.ProfitLossService", side_effect=mock_pl_factory),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [pond]
            MC.objects.return_value.only.return_value = [cycle]

            result = svc.get_report()

        assert result["total_revenue_idr"] == 55_000_000
        assert result["cycle_count"] == 1
        assert len(result["per_pond"]) == 1

    def test_no_active_cycles_raises(self):
        pond = self._make_pond("p1", "Pond Alpha")
        fake_farm = SimpleNamespace(id="farm_001", name="Test Farm", location="")

        from teramina.pl_report.services.farm_pl_service import FarmProfitLossService
        svc = FarmProfitLossService("farm_001")

        with (
            patch("teramina.pl_report.services.farm_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.farm_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.farm_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.farm_pl_service.ProfitLossService"),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [pond]
            MC.objects.return_value.only.return_value = []

            with pytest.raises(ValueError, match="No active cycle"):
                svc.get_report()


# ─── YearProfitLossService aggregate failures ─────────────────────────────────

class TestYearAggregateFailureBehaviour:

    _BASE_PATCHES = [
        "teramina.pl_report.services.year_pl_service.Farm",
        "teramina.pl_report.services.year_pl_service.Pond",
        "teramina.pl_report.services.year_pl_service.Cycle",
        "teramina.pl_report.services.year_pl_service.ResultData",
        "teramina.pl_report.services.year_pl_service.ProfitLossService",
    ]

    def _make_result_data(self, start="2024-03-01", doc_days=90):
        """Minimal result_data list with a parseable date on row[-1]."""
        return [
            {"doc": i + 1, "date": None}
            for i in range(doc_days - 1)
        ] + [{"doc": doc_days, "date": start}]

    def test_farm_not_found_raises(self):
        from teramina.pl_report.services.year_pl_service import YearProfitLossService
        svc = YearProfitLossService("ghost", 2024)
        with patch("teramina.pl_report.services.year_pl_service.Farm") as MF:
            MF.objects.return_value.first.return_value = None
            with pytest.raises(ValueError, match="not found"):
                svc.get_report()

    def test_no_ponds_raises(self):
        from teramina.pl_report.services.year_pl_service import YearProfitLossService
        fake_farm = SimpleNamespace(id="f1", name="F")
        svc = YearProfitLossService("f1", 2024)
        with (
            patch("teramina.pl_report.services.year_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.year_pl_service.Pond") as MP,
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = []
            with pytest.raises(ValueError, match="No ponds"):
                svc.get_report()

    def test_cycle_pl_failure_raises_with_name(self):
        from teramina.pl_report.services.year_pl_service import YearProfitLossService

        fake_farm = SimpleNamespace(id="f1", name="Farm")
        fake_pond = SimpleNamespace(id="p1", name="Pond X")
        fake_cycle = SimpleNamespace(
            id="c1", name="Cycle Boom", is_active=True,
            start_date=date(2024, 1, 1)
        )
        rd = SimpleNamespace(result_data=self._make_result_data("2024-06-01", 90))

        svc = YearProfitLossService("f1", 2024)

        with (
            patch("teramina.pl_report.services.year_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.year_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.year_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.year_pl_service.ResultData") as MR,
            patch("teramina.pl_report.services.year_pl_service.ProfitLossService") as MPS,
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [fake_pond]
            MC.objects.return_value.only.return_value = [fake_cycle]
            MR.objects.return_value.only.return_value.first.return_value = rd
            MPS.return_value.get_report.side_effect = RuntimeError("service exploded")

            with pytest.raises(ValueError) as exc_info:
                svc.get_report()

        msg = str(exc_info.value)
        assert "Cycle Boom" in msg
        assert "service exploded" in msg

    def test_no_overlapping_cycles_raises(self):
        from teramina.pl_report.services.year_pl_service import YearProfitLossService

        fake_farm = SimpleNamespace(id="f1", name="Farm")
        fake_pond = SimpleNamespace(id="p1", name="Pond X")
        # Cycle that ran entirely in 2022 — no overlap with 2024
        fake_cycle = SimpleNamespace(
            id="c1", name="Old Cycle", is_active=False,
            start_date=date(2022, 1, 1)
        )
        rd = SimpleNamespace(result_data=self._make_result_data("2022-06-01", 90))

        svc = YearProfitLossService("f1", 2024)

        with (
            patch("teramina.pl_report.services.year_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.year_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.year_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.year_pl_service.ResultData") as MR,
            patch("teramina.pl_report.services.year_pl_service.ProfitLossService"),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [fake_pond]
            MC.objects.return_value.only.return_value = [fake_cycle]
            MR.objects.return_value.only.return_value.first.return_value = rd

            with pytest.raises(ValueError, match="No cycle data overlapping year 2024"):
                svc.get_report()

    def test_cycle_with_no_result_data_is_silently_skipped(self):
        """A cycle that has no ResultData at all is not a P&L error; it's skipped."""
        from teramina.pl_report.services.year_pl_service import YearProfitLossService

        fake_farm = SimpleNamespace(id="f1", name="Farm")
        fake_pond = SimpleNamespace(id="p1", name="Pond X")
        fake_cycle = SimpleNamespace(
            id="c1", name="Empty Cycle", is_active=False,
            start_date=date(2024, 3, 1)
        )

        svc = YearProfitLossService("f1", 2024)

        with (
            patch("teramina.pl_report.services.year_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.year_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.year_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.year_pl_service.ResultData") as MR,
            patch("teramina.pl_report.services.year_pl_service.ProfitLossService"),
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [fake_pond]
            MC.objects.return_value.only.return_value = [fake_cycle]
            # No ResultData → should skip, not fail
            MR.objects.return_value.only.return_value.first.return_value = None

            # Raises "no overlapping" rather than a per-cycle error
            with pytest.raises(ValueError, match="No cycle data overlapping"):
                svc.get_report()

    def test_proration_calculated_correctly(self):
        """A cycle spanning full year 2024 should have proration=100%."""
        from teramina.pl_report.services.year_pl_service import YearProfitLossService

        fake_farm = SimpleNamespace(id="f1", name="Farm")
        fake_pond = SimpleNamespace(id="p1", name="Pond X")
        # Start Jan 1, end Dec 31 (366 days in 2024 — leap year)
        fake_cycle = SimpleNamespace(
            id="c1", name="Full Year", is_active=False,
            start_date=date(2024, 1, 1)
        )
        # last entry date = Dec 31
        rd = SimpleNamespace(result_data=[{"doc": 366, "date": "2024-12-31"}])
        report = _make_cycle_report()

        svc = YearProfitLossService("f1", 2024)

        with (
            patch("teramina.pl_report.services.year_pl_service.Farm") as MF,
            patch("teramina.pl_report.services.year_pl_service.Pond") as MP,
            patch("teramina.pl_report.services.year_pl_service.Cycle") as MC,
            patch("teramina.pl_report.services.year_pl_service.ResultData") as MR,
            patch("teramina.pl_report.services.year_pl_service.ProfitLossService") as MPS,
        ):
            MF.objects.return_value.first.return_value = fake_farm
            MP.objects.return_value.only.return_value = [fake_pond]
            MC.objects.return_value.only.return_value = [fake_cycle]
            MR.objects.return_value.only.return_value.first.return_value = rd
            MPS.return_value.get_report.return_value = report

            result = svc.get_report()

        # Proration for full year must be 100%
        assert result["per_cycle"][0]["proration_pct"] == pytest.approx(100.0, abs=0.1)
        assert result["year"] == 2024
