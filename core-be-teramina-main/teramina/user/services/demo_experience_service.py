from datetime import datetime

from teramina.cycle.models.cycle_model import Cycle
from teramina.dashboard.services.readiness import is_dashboard_ready_cycle
from teramina.farm.models.farm_model import Farm
from teramina.helpers.default_data_updater import DataSeeder
from teramina.helpers.demo_artifacts import DEMO_BUNDLE_VERSION
from teramina.pond.models.pond_model import Pond
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.demo_experience_model import DemoExperienceState, ProductEvent


EVENT_STEP_MAP = {
    "demo_today_opened": "review_today",
    "demo_assistant_question_sent": "ask_assistant",
    "demo_memory_opened": "open_memory",
    "demo_forecast_opened": "review_forecast",
    "demo_advisory_report_opened": "open_advisory_report",
    "demo_library_opened": "open_library",
    "real_data_activated": "add_real_farm",
}
ALLOWED_EVENTS = {
    "demo_opened",
    "demo_context_selected",
    "demo_checklist_step_completed",
    "demo_checklist_dismissed",
    "demo_checklist_reopened",
    "demo_reset",
    *EVENT_STEP_MAP.keys(),
}
ALLOWED_PROPERTIES = {"route", "scenario", "step"}


def _context(farm, pond, cycle):
    return {
        "farm_id": str(farm.id),
        "farm_name": farm.name,
        "pond_id": str(pond.id),
        "pond_name": pond.name,
        "cycle_id": str(cycle.id),
        "cycle_name": cycle.name,
    }


def _ready_context_for_farm(farm, preferred_scenario=""):
    ponds = list(Pond.objects(farm_id=str(farm.id), archived_at=None).order_by("name"))
    if preferred_scenario:
        ponds.sort(key=lambda item: item.demo_scenario != preferred_scenario)
    for pond in ponds:
        cycles = list(Cycle.objects(pond_id=str(pond.id), archived_at=None).order_by("-start_date"))
        for cycle in cycles:
            if is_dashboard_ready_cycle(str(cycle.id)):
                return _context(farm, pond, cycle)
    return None


def user_has_real_dashboard_data(user_id):
    for farm in Farm.objects(user_id=str(user_id), archived_at=None, demo_bundle_version__in=["", None]).order_by("-created_at"):
        if _ready_context_for_farm(farm):
            return True
    return False


class DemoExperienceService:
    @staticmethod
    def _state(user_id):
        return DemoExperienceState.objects(user_id=user_id).modify(
            upsert=True,
            new=True,
            set_on_insert__bundle_version=DEMO_BUNDLE_VERSION,
            set_on_insert__completed_steps=[],
            set_on_insert__seen_scenarios=[],
            set_on_insert__created_at=datetime.utcnow(),
            set__updated_at=datetime.utcnow(),
        )

    @staticmethod
    def _payload(user_id, state=None):
        state = state or DemoExperienceService._state(user_id)
        demo_farm = Farm.objects(
            user_id=user_id, demo_bundle_version=DEMO_BUNDLE_VERSION, archived_at=None
        ).first()
        real_context = None
        for farm in Farm.objects(user_id=user_id, demo_bundle_version__in=["", None], archived_at=None).order_by("-created_at"):
            real_context = _ready_context_for_farm(farm)
            if real_context:
                break
        demo_context = _ready_context_for_farm(demo_farm, "at_risk") if demo_farm else None
        return {
            "demo_available": bool(demo_context),
            "bundle_version": DEMO_BUNDLE_VERSION if demo_context else "",
            "has_real_data": bool(real_context),
            "default_context": real_context or demo_context,
            "demo_context": demo_context,
            "first_opened_at": state.first_opened_at.isoformat() if state.first_opened_at else None,
            "checklist_dismissed": state.checklist_dismissed,
            "completed_steps": list(state.completed_steps or []),
            "seen_scenarios": list(state.seen_scenarios or []),
            "reset_count": state.reset_count,
        }

    @staticmethod
    def get(user_id):
        return 200, DataSuccessSchema(code=200, message="OK", payload=DemoExperienceService._payload(user_id))

    @staticmethod
    def record_event(user_id, event_name, properties):
        if event_name not in ALLOWED_EVENTS:
            return 400, DataErrorSchema(code=400, message="Unsupported demo experience event")
        clean_properties = {key: value for key, value in (properties or {}).items() if key in ALLOWED_PROPERTIES and isinstance(value, str)}
        ProductEvent(user_id=user_id, event_name=event_name, properties=clean_properties).save()
        state = DemoExperienceService._state(user_id)
        completed = set(state.completed_steps or [])
        scenarios = set(state.seen_scenarios or [])
        step = EVENT_STEP_MAP.get(event_name)
        if event_name == "demo_checklist_step_completed":
            step = clean_properties.get("step")
        if step:
            completed.add(step)
        if event_name == "demo_context_selected" and clean_properties.get("scenario") in {"healthy", "at_risk"}:
            scenarios.add(clean_properties["scenario"])
            if scenarios == {"healthy", "at_risk"}:
                completed.add("compare_scenarios")
        if event_name == "demo_opened" and not state.first_opened_at:
            state.first_opened_at = datetime.utcnow()
        state.completed_steps = sorted(completed)
        state.seen_scenarios = sorted(scenarios)
        state.updated_at = datetime.utcnow()
        state.save()
        return 200, DataSuccessSchema(code=200, message="Event recorded", payload=DemoExperienceService._payload(user_id, state))

    @staticmethod
    def update(user_id, checklist_dismissed):
        state = DemoExperienceService._state(user_id)
        state.checklist_dismissed = checklist_dismissed
        state.updated_at = datetime.utcnow()
        state.save()
        return 200, DataSuccessSchema(code=200, message="Demo experience updated", payload=DemoExperienceService._payload(user_id, state))

    @staticmethod
    def reset(user_id, confirmed):
        if not confirmed:
            return 400, DataErrorSchema(code=400, message="Reset confirmation is required")
        demo_farm = Farm.objects(user_id=user_id, demo_bundle_version=DEMO_BUNDLE_VERSION).first()
        source_farm = Farm.objects(user_id="__seed__", demo_bundle_version=DEMO_BUNDLE_VERSION).order_by("-created_at").first()
        if not demo_farm or not source_farm:
            return 400, DataErrorSchema(code=400, message="Demo bundle is not available")
        seeder = DataSeeder(str(source_farm.id), user_id=user_id)
        seeder.repair_existing_data()
        state = DemoExperienceService._state(user_id)
        state.reset_count += 1
        state.updated_at = datetime.utcnow()
        state.save()
        ProductEvent(user_id=user_id, event_name="demo_reset", properties={}).save()
        return 200, DataSuccessSchema(code=200, message="Demo reset", payload=DemoExperienceService._payload(user_id, state))
