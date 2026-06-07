"""Validate all user-facing modules against synchronized demo scenarios."""

from datetime import date, datetime

from django.core.management.base import BaseCommand

from teramina.advisory.models.advisory_model import AdvisoryCase, AdvisoryReport
from teramina.agent.models.agent_model import AgentMemory, FarmAlert, WorkflowTask
from teramina.agent.services.agent_service import AgentService
from teramina.content.models.content_model import ContentAccess
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData, ResultData
from teramina.dashboard.services.filter_service import FilterData
from teramina.dashboard.services.forecast_service import ForecastDataService
from teramina.dashboard.services.historical.economic import DashboardEconomic
from teramina.dashboard.services.historical.feed import DashboardFeed
from teramina.dashboard.services.historical.overview import DashboardOverview
from teramina.farm.models.farm_model import Farm
from teramina.harvest.services.harvest_service import HarvestService
from teramina.helpers.demo_artifacts import DEMO_BUNDLE_VERSION, DEMO_TAG
from teramina.pond.models.pond_model import Pond
from teramina.user.models.user_model import User
from teramina.water_quality_dashboard.services.water_quality_service import WaterQuality


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _check(result):
    status, response = result
    return {"status": status, "message": response.message}


class Command(BaseCommand):
    help = "Validate the synchronized A/B demo bundle for application users."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="", help="Validate one application user by email")
        parser.add_argument("--include-template", action="store_true", help="Also validate the __seed__ template bundle")

    def handle(self, *args, **options):
        users = User.objects(email=options["email"]) if options["email"] else User.objects()
        entries = [(user.email, str(user.id), True) for user in users]
        if options["include_template"]:
            entries.append(("__seed__", "__seed__", False))
        checked = failures = 0
        for email, user_id, require_linked in entries:
            farm = Farm.objects(user_id=user_id, demo_bundle_version=DEMO_BUNDLE_VERSION).first()
            if not farm:
                self.stderr.write(f"{email}: missing {DEMO_BUNDLE_VERSION} demo farm")
                failures += 1
                continue

            scenario_results = {}
            for pond in Pond.objects(farm_id=str(farm.id)):
                cycle = Cycle.objects(id=pond.active_cycle_id, pond_id=str(pond.id), is_active=True).first()
                if not cycle:
                    scenario_results[pond.demo_scenario] = {"error": "missing active cycle"}
                    failures += 1
                    continue
                cycle_id = str(cycle.id)
                cycle_data = CycleData.objects(cycle_id=cycle_id).first()
                result_data = ResultData.objects(cycle_id=cycle_id).first()
                forecast_data = ForecastData.objects(cycle_id=cycle_id).first()
                start_date = _as_date(cycle_data.result_data[0]["date"])
                end_date = _as_date(cycle_data.result_data[-1]["date"])
                end_date_query = end_date.strftime("%m/%d/%Y")
                forecast_filter = FilterData(user_id).filter(str(farm.id), str(pond.id), cycle_id, "forecast")
                forecast_date = (
                    forecast_filter[1].payload[0]["daterange"]["end_date"]
                    if forecast_filter[0] == 200
                    else None
                )
                checks = {
                    "forecast_filter": _check(forecast_filter),
                    "overview": _check(DashboardOverview(str(farm.id), str(pond.id), cycle_id, end_date_query).overview()),
                    "economics": _check(DashboardEconomic(str(farm.id), str(pond.id), cycle_id, end_date_query).economic()),
                    "feeding": _check(DashboardFeed(str(farm.id), str(pond.id), cycle_id, end_date_query).feed()),
                    "forecast": _check(ForecastDataService().get_forecasting_overview(cycle_id, forecast_date)),
                    "harvest_record": _check(HarvestService(cycle_id).get_harvest_record()),
                    "harvest_recommendation": _check(HarvestService(cycle_id).get_harvest_recommendation()),
                    "water_quality": _check(
                        WaterQuality().get_water_quality_data(cycle_id, start_date.isoformat(), end_date.isoformat(), "wqi_1")
                    ),
                }
                rows_ok = (
                    len(cycle_data.result_data if cycle_data else []) == 60
                    and len(result_data.result_data if result_data else []) == 60
                    and len(forecast_data.result_data if forecast_data else []) >= 120
                )
                if not rows_ok or any(check["status"] != 200 for check in checks.values()):
                    failures += 1
                scenario_results[pond.demo_scenario] = {"rows_ok": rows_ok, **checks}
                checked += 1

            today_status = AgentService.get_today_summary(user_id, str(farm.id))[0] if require_linked else None
            linked = {}
            if require_linked:
                linked = {
                    "alerts": FarmAlert.objects(user_id=user_id, data__demo_bundle_version=DEMO_BUNDLE_VERSION).count(),
                    "tasks": WorkflowTask.objects(user_id=user_id, title__startswith="[Demo]").count(),
                    "memories": AgentMemory.objects(user_id=user_id, tags=DEMO_TAG).count(),
                    "content_access": ContentAccess.objects(user_id=user_id).count(),
                    "advisory_cases": AdvisoryCase.objects(user_id=user_id, intake_data__demo_bundle_version=DEMO_BUNDLE_VERSION).count(),
                    "advisory_reports": AdvisoryReport.objects(user_id=user_id, status="delivered").count(),
                }
            linked_failed = require_linked and (today_status != 200 or any(value < 1 for value in linked.values()))
            if set(scenario_results) != {"healthy", "at_risk"} or linked_failed:
                failures += 1
            self.stdout.write(str({
                "user": email,
                "today": today_status,
                "scenarios": scenario_results,
                "linked": linked,
            }))

        self.stdout.write(f"Demo bundle validation complete: scenarios_checked={checked} failures={failures}")
        if failures:
            raise RuntimeError(f"Demo bundle validation failed with {failures} issue(s)")
