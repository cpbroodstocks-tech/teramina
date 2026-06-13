import os
from datetime import datetime
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from mongoengine.errors import NotUniqueError, ValidationError

from teramina.content.models.content_model import ContentItem
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.advisory_model import (
    AdvisoryAssistantBriefLog,
    AdvisoryCase,
    AdvisoryAssistantAnswerLog,
    AdvisoryExpertReview,
    AdvisoryReport,
    AdvisoryReportWorkflowEvent,
    BenchmarkConsentRecord,
    HatcheryOperationalRecord,
    HatcheryProfile,
    InvestorDueDiligenceScore,
    PhaseSixRecordRevision,
    RetainerCadence,
    ServicePackage,
)
from .advisory_retrieval_service import AdvisoryRetrievalService


def _is_admin(user) -> bool:
    return getattr(user, "role_user", "") == "admin"


def _can_access_case(user, case: AdvisoryCase) -> bool:
    return _is_admin(user) or str(user.id) == case.user_id


CASE_REQUIRED_INTAKE = {
    "farm_diagnostic": [
        "farm_name_location",
        "stocking_date",
        "pond_size",
        "stocking_density",
        "pl_source",
        "feed_data_summary",
        "water_quality_summary",
        "mortality_timeline",
        "disease_test_results",
        "main_question",
    ],
    "crop_planning": [
        "farm_pond_details",
        "planned_stocking_date",
        "target_density",
        "pl_source",
        "survival_fcr_assumptions",
        "cost_assumptions",
        "market_price_assumptions",
        "main_planning_concern",
    ],
    "hatchery_review": [
        "hatchery_name_location",
        "broodstock_source",
        "quarantine_acclimation_summary",
        "mating_rate",
        "spawning_rate",
        "nauplii_per_spawn",
        "hatching_rate",
        "pl_quality_testing_notes",
        "main_performance_concern",
    ],
    "procurement_advisory": [
        "buyer_profile",
        "material_needed",
        "target_supplier_options",
        "genetic_trait_priority",
        "biosecurity_requirements",
        "procurement_timeline",
        "main_procurement_question",
    ],
    "investor_due_diligence": [
        "project_type",
        "location",
        "planned_capacity",
        "capex_estimate",
        "opex_estimate",
        "management_team_background",
        "technical_assumptions",
        "main_investment_question",
    ],
    "retainer": [
        "organization_profile",
        "sites_scope",
        "support_cadence",
        "active_problem",
        "data_available",
        "monthly_goals",
    ],
}

CASE_REFERENCE_CATEGORIES = {
    "farm_diagnostic": {"Farm", "Disease", "Management"},
    "crop_planning": {"Farm", "Economics", "Management"},
    "hatchery_review": {"Hatchery", "Management"},
    "procurement_advisory": {"Genetics", "Hatchery", "Farm"},
    "investor_due_diligence": {"Economics", "Management", "Farm"},
    "retainer": {"Management", "Farm", "Hatchery"},
}

CASE_MAIN_QUESTION_KEYS = {
    "farm_diagnostic": "main_question",
    "crop_planning": "main_planning_concern",
    "hatchery_review": "main_performance_concern",
    "procurement_advisory": "main_procurement_question",
    "investor_due_diligence": "main_investment_question",
    "retainer": "active_problem",
}

BENCHMARK_CONSENT_TYPE = "phase_six_benchmark"
BENCHMARK_TERMS_VERSION = "phase-six-benchmark-v1"
BENCHMARK_TERMS_TEXT = (
    "I allow Teramina to use this case's approved Phase 6 hatchery and investor records in anonymized aggregate benchmarks. "
    "Teramina will not disclose farm, hatchery, company, location, or personal identity without separate written permission."
)


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _humanize_key(value: str) -> str:
    return value.replace("_", " ").title()


def _short_value(value, limit=180) -> str:
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        value = ", ".join(f"{key}: {val}" for key, val in value.items())
    else:
        value = str(value)
    return value if len(value) <= limit else f"{value[:limit].rstrip()}..."


def _score(value) -> float:
    try:
        return max(0, min(float(value or 0), 100))
    except (TypeError, ValueError):
        return 0


def _risk_level(score: float) -> str:
    if score >= 80:
        return "low"
    if score >= 60:
        return "moderate"
    if score >= 40:
        return "high"
    return "critical"


class AdvisoryService:
    REPORT_STATUSES = {"draft", "expert_review_required", "delivered"}

    @staticmethod
    def list_packages(active_only=True):
        query = {"is_active": True} if active_only else {}
        packages = [pkg.to_dict() for pkg in ServicePackage.objects(**query).order_by("sort_order", "name")]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"packages": packages})

    @staticmethod
    def get_package(slug: str):
        package = ServicePackage.objects(slug=slug, is_active=True).first()
        if not package:
            return 404, DataErrorSchema(code=404, message="Service package not found")
        return 200, DataSuccessSchema(code=200, message="OK", payload={"package": package.to_dict()})

    @staticmethod
    def create_package(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        try:
            package = ServicePackage(**data.dict())
            package.save()
            return 200, DataSuccessSchema(code=200, message="Service package created", payload={"package": package.to_dict()})
        except (NotUniqueError, ValidationError) as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def create_case(user_id: str, data):
        package_id = data.service_package_id or ""
        if package_id and not ServicePackage.objects(id=package_id, is_active=True).first():
            return 400, DataErrorSchema(code=400, message="Service package is not available")

        case = AdvisoryCase(
            user_id=user_id,
            service_package_id=package_id,
            case_type=data.case_type,
            farm_id=data.farm_id or "",
            pond_id=data.pond_id or "",
            cycle_id=data.cycle_id or "",
            title=data.title or data.case_type.replace("_", " ").title(),
            intake_data=data.intake_data or {},
            uploaded_files=[],
        )
        try:
            case.save()
            if data.uploaded_files:
                case.uploaded_files = [
                    AdvisoryService._normalize_case_file(file_ref, case, user_id)
                    for file_ref in data.uploaded_files
                ]
                case.updated_at = datetime.now()
                case.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))
        return 200, DataSuccessSchema(code=200, message="Advisory case created", payload={"case": case.to_dict()})

    @staticmethod
    def list_cases(user_id: str):
        cases = [case.to_dict() for case in AdvisoryCase.objects(user_id=user_id).order_by("-created_at")]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"cases": cases})

    @staticmethod
    def list_history(user, farm_id="", pond_id="", cycle_id="", limit=50):
        if not farm_id and not pond_id and not cycle_id:
            return 400, DataErrorSchema(code=400, message="At least one farm, pond, or cycle filter is required")

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        query = {}
        if not _is_admin(user):
            query["user_id"] = str(user.id)
        if farm_id:
            query["farm_id"] = farm_id
        if pond_id:
            query["pond_id"] = pond_id
        if cycle_id:
            query["cycle_id"] = cycle_id

        cases = AdvisoryCase.objects(**query).order_by("-created_at")[:limit]
        events = [AdvisoryService._case_to_history_event(case) for case in cases]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"total_events": len(events), "events": events})

    @staticmethod
    def _case_to_history_event(case: AdvisoryCase):
        case_type_label = case.case_type.replace("_", " ").title()
        title = case.title or case_type_label
        return {
            "id": str(case.id),
            "source": "advisory",
            "type": "advisory_case",
            "case_id": str(case.id),
            "case_type": case.case_type,
            "status": case.status,
            "title": title,
            "description": f"{case_type_label}: {title}",
            "farm_id": case.farm_id,
            "pond_id": case.pond_id,
            "cycle_id": case.cycle_id,
            "report_id": case.report_id,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
            "url": f"/dashboard/advisory/{str(case.id)}",
        }

    @staticmethod
    def admin_list_cases(user, status="", case_type=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status
        if case_type:
            query["case_type"] = case_type

        cases = [
            case.to_dict(include_private=True)
            for case in AdvisoryCase.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"cases": cases})

    @staticmethod
    def admin_list_assistant_brief_logs(user, case_id="", status="", limit=50):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if case_id:
            query["case_id"] = case_id
        if status:
            query["status"] = status

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        logs = [
            log.to_dict()
            for log in AdvisoryAssistantBriefLog.objects(**query).order_by("-created_at")[:limit]
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"logs": logs})

    @staticmethod
    def admin_list_assistant_answer_logs(user, case_id="", asked_by="", limit=50):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if case_id:
            query["case_id"] = case_id
        if asked_by:
            query["asked_by"] = asked_by

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        logs = [
            log.to_dict()
            for log in AdvisoryAssistantAnswerLog.objects(**query).order_by("-created_at")[:limit]
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"logs": logs})

    @staticmethod
    def admin_list_report_workflow_events(user, report_id="", case_id="", limit=50):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if report_id:
            query["report_id"] = report_id
        if case_id:
            query["case_id"] = case_id

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        events = [
            event.to_dict()
            for event in AdvisoryReportWorkflowEvent.objects(**query).order_by("-changed_at")[:limit]
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"events": events})

    @staticmethod
    def create_hatchery_profile(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        case = AdvisoryCase.objects(id=data.case_id).first() if data.case_id else None
        if data.case_id and not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        owner_id = case.user_id if case else (data.user_id or "")
        if not owner_id:
            return 400, DataErrorSchema(code=400, message="User or advisory case is required")

        profile = HatcheryProfile(
            user_id=owner_id,
            case_id=data.case_id or "",
            name=data.name,
            location=data.location,
            maturation_capacity=data.maturation_capacity,
            larval_capacity=data.larval_capacity,
            biosecurity_level=data.biosecurity_level,
            water_source=data.water_source,
            notes=data.notes,
            client_visible=data.client_visible,
            created_by=str(user.id),
        )
        try:
            profile.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))
        return 200, DataSuccessSchema(
            code=200,
            message="Hatchery profile created",
            payload={"hatchery": profile.to_dict(include_private=True)},
        )

    @staticmethod
    def admin_list_hatchery_profiles(user, case_id="", user_id=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if case_id:
            query["case_id"] = case_id
        if user_id:
            query["user_id"] = user_id
        hatcheries = [
            profile.to_dict(include_private=True)
            for profile in HatcheryProfile.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"hatcheries": hatcheries})

    @staticmethod
    def update_hatchery_profile(user, hatchery_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        profile = HatcheryProfile.objects(id=hatchery_id).first()
        if not profile:
            return 404, DataErrorSchema(code=404, message="Hatchery profile not found")

        previous_data = profile.to_dict(include_private=True)
        profile.name = data.name
        profile.location = data.location
        profile.maturation_capacity = data.maturation_capacity
        profile.larval_capacity = data.larval_capacity
        profile.biosecurity_level = data.biosecurity_level
        profile.water_source = data.water_source
        profile.notes = data.notes
        profile.client_visible = data.client_visible
        profile.updated_at = datetime.now()
        try:
            profile.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        revision = AdvisoryService._log_phase_six_revision(
            "hatchery_profile",
            profile,
            previous_data,
            profile.to_dict(include_private=True),
            str(user.id),
            data.change_note or "Updated hatchery profile",
        )
        return 200, DataSuccessSchema(
            code=200,
            message="Hatchery profile updated",
            payload={"hatchery": profile.to_dict(include_private=True), "revision": revision.to_dict()},
        )

    @staticmethod
    def create_hatchery_record(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        hatchery = HatcheryProfile.objects(id=data.hatchery_id).first()
        if not hatchery:
            return 404, DataErrorSchema(code=404, message="Hatchery profile not found")

        case_id = data.case_id or hatchery.case_id
        if case_id:
            case = AdvisoryCase.objects(id=case_id).first()
            if not case:
                return 404, DataErrorSchema(code=404, message="Advisory case not found")
            if case.user_id != hatchery.user_id:
                return 400, DataErrorSchema(code=400, message="Hatchery and advisory case users do not match")

        record = HatcheryOperationalRecord(
            hatchery_id=data.hatchery_id,
            case_id=case_id,
            user_id=hatchery.user_id,
            record_type=data.record_type,
            record_date=data.record_date,
            batch_code=data.batch_code,
            broodstock_source=data.broodstock_source,
            metrics=data.metrics or {},
            notes=data.notes,
            client_visible=data.client_visible,
            created_by=str(user.id),
        )
        try:
            record.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))
        hatchery.updated_at = datetime.now()
        hatchery.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Hatchery operational record created",
            payload={"record": record.to_dict(include_private=True)},
        )

    @staticmethod
    def admin_list_hatchery_records(user, hatchery_id="", case_id="", record_type=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if hatchery_id:
            query["hatchery_id"] = hatchery_id
        if case_id:
            query["case_id"] = case_id
        if record_type:
            query["record_type"] = record_type
        records = [
            record.to_dict(include_private=True)
            for record in HatcheryOperationalRecord.objects(**query).order_by("-record_date", "-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"records": records})

    @staticmethod
    def update_hatchery_record(user, record_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        record = HatcheryOperationalRecord.objects(id=record_id).first()
        if not record:
            return 404, DataErrorSchema(code=404, message="Hatchery operational record not found")

        previous_data = record.to_dict(include_private=True)
        record.record_type = data.record_type
        record.record_date = data.record_date
        record.batch_code = data.batch_code
        record.broodstock_source = data.broodstock_source
        record.metrics = data.metrics or {}
        record.notes = data.notes
        record.client_visible = data.client_visible
        record.updated_at = datetime.now()
        try:
            record.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        revision = AdvisoryService._log_phase_six_revision(
            "hatchery_record",
            record,
            previous_data,
            record.to_dict(include_private=True),
            str(user.id),
            data.change_note or "Updated hatchery operational record",
        )
        return 200, DataSuccessSchema(
            code=200,
            message="Hatchery operational record updated",
            payload={"record": record.to_dict(include_private=True), "revision": revision.to_dict()},
        )

    @staticmethod
    def create_investor_due_diligence_score(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        case = AdvisoryCase.objects(id=data.case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if case.case_type != "investor_due_diligence":
            return 400, DataErrorSchema(code=400, message="Case is not an investor due-diligence case")

        scores = [
            _score(data.technical_score),
            _score(data.management_score),
            _score(data.biosecurity_score),
            _score(data.market_score),
            _score(data.financial_score),
        ]
        overall = round(sum(scores) / len(scores), 2)
        score = InvestorDueDiligenceScore(
            case_id=data.case_id,
            user_id=case.user_id,
            project_type=data.project_type,
            location=data.location,
            planned_capacity=data.planned_capacity,
            capex_estimate_idr=data.capex_estimate_idr,
            opex_estimate_idr=data.opex_estimate_idr,
            technical_score=scores[0],
            management_score=scores[1],
            biosecurity_score=scores[2],
            market_score=scores[3],
            financial_score=scores[4],
            overall_score=overall,
            risk_level=_risk_level(overall),
            red_flags=data.red_flags or [],
            recommendations=data.recommendations or [],
            assumptions=data.assumptions or [],
            client_visible=data.client_visible,
            created_by=str(user.id),
        )
        try:
            score.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))
        case.status = "in_review" if case.status == "inquiry" else case.status
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Investor due-diligence score created",
            payload={"score": score.to_dict(include_private=True)},
        )

    @staticmethod
    def admin_list_investor_due_diligence_scores(user, case_id="", risk_level=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if case_id:
            query["case_id"] = case_id
        if risk_level:
            query["risk_level"] = risk_level
        scores = [
            score.to_dict(include_private=True)
            for score in InvestorDueDiligenceScore.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"scores": scores})

    @staticmethod
    def update_investor_due_diligence_score(user, score_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        score = InvestorDueDiligenceScore.objects(id=score_id).first()
        if not score:
            return 404, DataErrorSchema(code=404, message="Investor due-diligence score not found")

        previous_data = score.to_dict(include_private=True)
        scores = [
            _score(data.technical_score),
            _score(data.management_score),
            _score(data.biosecurity_score),
            _score(data.market_score),
            _score(data.financial_score),
        ]
        score.project_type = data.project_type
        score.location = data.location
        score.planned_capacity = data.planned_capacity
        score.capex_estimate_idr = data.capex_estimate_idr
        score.opex_estimate_idr = data.opex_estimate_idr
        score.technical_score = scores[0]
        score.management_score = scores[1]
        score.biosecurity_score = scores[2]
        score.market_score = scores[3]
        score.financial_score = scores[4]
        score.overall_score = round(sum(scores) / len(scores), 2)
        score.risk_level = _risk_level(score.overall_score)
        score.red_flags = data.red_flags or []
        score.recommendations = data.recommendations or []
        score.assumptions = data.assumptions or []
        score.client_visible = data.client_visible
        score.updated_at = datetime.now()
        try:
            score.save()
        except ValidationError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        revision = AdvisoryService._log_phase_six_revision(
            "investor_score",
            score,
            previous_data,
            score.to_dict(include_private=True),
            str(user.id),
            data.change_note or "Updated investor due-diligence score",
        )
        return 200, DataSuccessSchema(
            code=200,
            message="Investor due-diligence score updated",
            payload={"score": score.to_dict(include_private=True), "revision": revision.to_dict()},
        )

    @staticmethod
    def admin_list_phase_six_revisions(user, record_kind="", record_id="", case_id="", limit=50):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if record_kind:
            query["record_kind"] = record_kind
        if record_id:
            query["record_id"] = record_id
        if case_id:
            query["case_id"] = case_id

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        revisions = [
            revision.to_dict()
            for revision in PhaseSixRecordRevision.objects(**query).order_by("-created_at")[:limit]
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"revisions": revisions})

    @staticmethod
    def _log_phase_six_revision(record_kind, record, previous_data, new_data, changed_by, change_note):
        revision_number = PhaseSixRecordRevision.objects(record_kind=record_kind, record_id=str(record.id)).count() + 1
        revision = PhaseSixRecordRevision(
            record_kind=record_kind,
            record_id=str(record.id),
            case_id=getattr(record, "case_id", "") or "",
            user_id=getattr(record, "user_id", "") or "",
            revision_number=revision_number,
            previous_data=previous_data,
            new_data=new_data,
            change_note=change_note,
            changed_by=changed_by,
        )
        revision.save()
        return revision

    @staticmethod
    def create_report_from_investor_score(user, score_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        score = InvestorDueDiligenceScore.objects(id=score_id).first()
        if not score:
            return 404, DataErrorSchema(code=404, message="Investor due-diligence score not found")
        case = AdvisoryCase.objects(id=score.case_id, user_id=score.user_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if data.status not in ["draft", "expert_review_required"]:
            return 400, DataErrorSchema(code=400, message="Investor score reports require expert review before delivery")

        report = AdvisoryReport(
            case_id=score.case_id,
            user_id=score.user_id,
            title=f"Investor Due Diligence Draft: {case.title or score.project_type.title()}",
            executive_summary=(
                f"Internal due-diligence draft for a {score.project_type} project in {score.location or 'the target region'}. "
                f"Overall score is {score.overall_score} with {score.risk_level} risk."
            ),
            data_received=[
                f"Project type: {score.project_type}",
                f"Location: {score.location or '-'}",
                f"Planned capacity: {score.planned_capacity or '-'}",
                f"Capex estimate IDR: {score.capex_estimate_idr or '-'}",
                f"Opex estimate IDR: {score.opex_estimate_idr or '-'}",
            ],
            key_findings=[
                f"Technical score: {score.technical_score}",
                f"Management score: {score.management_score}",
                f"Biosecurity score: {score.biosecurity_score}",
                f"Market score: {score.market_score}",
                f"Financial score: {score.financial_score}",
                f"Overall risk level: {score.risk_level}",
            ],
            likely_causes=list(score.red_flags or []),
            technical_interpretation=(
                "This score is a structured internal investment screen. It does not replace expert review, legal review, "
                "or verified engineering and financial due diligence."
            ),
            economic_implication=(
                f"Capex and opex assumptions should be stress-tested against survival, FCR, price, utilization, and ramp-up sensitivity. "
                f"Current financial score is {score.financial_score}."
            ),
            corrective_action_plan=list(score.recommendations or []),
            monitoring_plan=[
                "Validate project assumptions against engineering drawings, production model, and management capacity.",
                "Review biosecurity and disease-risk controls before investment close.",
                "Run downside sensitivity before final go/no-go recommendation.",
            ],
            assumptions_and_limits=list(score.assumptions or []) + [
                "Generated from structured investor due-diligence scores.",
                "Internal draft only until reviewed and delivered through the advisory report workflow.",
            ],
            status=data.status,
        )
        report.save()
        case.report_id = str(report.id)
        case.status = "in_review"
        case.updated_at = datetime.now()
        case.save()
        AdvisoryService._log_report_workflow_event(
            report,
            previous_status="",
            new_status=report.status,
            review_note=data.review_note or f"Created from investor score {score_id}.",
            changed_by=str(user.id),
        )
        return 200, DataSuccessSchema(
            code=200,
            message="Investor due-diligence report draft created",
            payload={"report": report.to_dict(include_private=True), "score": score.to_dict(include_private=True)},
        )

    @staticmethod
    def admin_phase_six_benchmarks(user, record_type="", risk_level="", project_type="", from_month="", to_month=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        if not AdvisoryService._is_valid_benchmark_month(from_month) or not AdvisoryService._is_valid_benchmark_month(to_month):
            return 400, DataErrorSchema(code=400, message="Benchmark month filters must use YYYY-MM format")

        active_consents = BenchmarkConsentRecord.objects(consent_type=BENCHMARK_CONSENT_TYPE, status="active")
        consented_case_ids = sorted({consent.case_id for consent in active_consents})
        hatchery_records = list(HatcheryOperationalRecord.objects(case_id__in=consented_case_ids))
        investor_scores = list(InvestorDueDiligenceScore.objects(case_id__in=consented_case_ids))

        hatchery_records = [
            record
            for record in hatchery_records
            if (not record_type or record.record_type == record_type)
            and AdvisoryService._is_in_benchmark_month_range(record.record_date or record.created_at, from_month, to_month)
        ]
        investor_scores = [
            score
            for score in investor_scores
            if (not risk_level or score.risk_level == risk_level)
            and (not project_type or score.project_type == project_type)
            and AdvisoryService._is_in_benchmark_month_range(score.created_at, from_month, to_month)
        ]

        record_type_counts = {}
        pl_quality_scores = []
        for record in hatchery_records:
            record_type_counts[record.record_type] = record_type_counts.get(record.record_type, 0) + 1
            value = (record.metrics or {}).get("pl_quality_score")
            if isinstance(value, (int, float)):
                pl_quality_scores.append(float(value))

        risk_counts = {}
        for score in investor_scores:
            risk_counts[score.risk_level] = risk_counts.get(score.risk_level, 0) + 1
        average_investor_score = (
            round(sum(score.overall_score for score in investor_scores) / len(investor_scores), 2)
            if investor_scores
            else None
        )
        trend = AdvisoryService._phase_six_benchmark_trend(hatchery_records, investor_scores)
        filtered_case_ids = sorted(
            {record.case_id for record in hatchery_records if record.case_id}
            | {score.case_id for score in investor_scores if score.case_id}
        )

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "benchmark_scope": "consented_phase_six_records",
                "source_case_count": len(filtered_case_ids),
                "total_consented_case_count": len(consented_case_ids),
                "filters": {
                    "record_type": record_type,
                    "risk_level": risk_level,
                    "project_type": project_type,
                    "from_month": from_month,
                    "to_month": to_month,
                },
                "hatchery": {
                    "record_count": len(hatchery_records),
                    "record_type_counts": record_type_counts,
                    "average_pl_quality_score": round(sum(pl_quality_scores) / len(pl_quality_scores), 2) if pl_quality_scores else None,
                },
                "investor": {
                    "score_count": len(investor_scores),
                    "risk_level_counts": risk_counts,
                    "average_overall_score": average_investor_score,
                },
                "trend": trend,
            },
        )

    @staticmethod
    def _is_valid_benchmark_month(value):
        if not value:
            return True
        parts = value.split("-")
        if len(parts) != 2:
            return False
        year, month = parts
        if len(year) != 4 or len(month) != 2 or not year.isdigit() or not month.isdigit():
            return False
        return 1 <= int(month) <= 12

    @staticmethod
    def _benchmark_month_key(value):
        return value.strftime("%Y-%m") if value else ""

    @staticmethod
    def _is_in_benchmark_month_range(value, from_month="", to_month=""):
        month = AdvisoryService._benchmark_month_key(value)
        if from_month and month < from_month:
            return False
        if to_month and month > to_month:
            return False
        return True

    @staticmethod
    def _phase_six_benchmark_trend(hatchery_records, investor_scores):
        months = {}
        for record in hatchery_records:
            month = AdvisoryService._benchmark_month_key(record.record_date or record.created_at)
            bucket = months.setdefault(month, {"pl_quality_scores": [], "investor_scores": [], "hatchery_record_count": 0})
            bucket["hatchery_record_count"] += 1
            value = (record.metrics or {}).get("pl_quality_score")
            if isinstance(value, (int, float)):
                bucket["pl_quality_scores"].append(float(value))

        for score in investor_scores:
            month = AdvisoryService._benchmark_month_key(score.created_at)
            bucket = months.setdefault(month, {"pl_quality_scores": [], "investor_scores": [], "hatchery_record_count": 0})
            bucket["investor_scores"].append(float(score.overall_score))

        trend = []
        for month in sorted(months):
            bucket = months[month]
            pl_scores = bucket["pl_quality_scores"]
            investor_values = bucket["investor_scores"]
            trend.append({
                "month": month,
                "hatchery_record_count": bucket["hatchery_record_count"],
                "average_pl_quality_score": round(sum(pl_scores) / len(pl_scores), 2) if pl_scores else None,
                "investor_score_count": len(investor_values),
                "average_overall_score": round(sum(investor_values) / len(investor_values), 2) if investor_values else None,
            })
        return trend

    @staticmethod
    def get_benchmark_consent(user, case_id: str):
        case = AdvisoryCase.objects(id=case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if not _can_access_case(user, case):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={"benchmark_consent": AdvisoryService._benchmark_consent_state(case)},
        )

    @staticmethod
    def accept_benchmark_consent(user, case_id: str, data):
        case = AdvisoryCase.objects(id=case_id, user_id=str(user.id)).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        active = AdvisoryService._active_benchmark_consent(case)
        if active:
            return 200, DataSuccessSchema(
                code=200,
                message="Benchmark consent already active",
                payload={"benchmark_consent": AdvisoryService._benchmark_consent_state(case)},
            )

        terms_version = data.terms_version or BENCHMARK_TERMS_VERSION
        consent = BenchmarkConsentRecord(
            case_id=str(case.id),
            user_id=case.user_id,
            terms_version=terms_version,
            terms_text=BENCHMARK_TERMS_TEXT,
            accepted_by=str(user.id),
        )
        consent.save()
        case.benchmark_consent = True
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Benchmark consent accepted",
            payload={"benchmark_consent": AdvisoryService._benchmark_consent_state(case)},
        )

    @staticmethod
    def revoke_benchmark_consent(user, case_id: str):
        case = AdvisoryCase.objects(id=case_id, user_id=str(user.id)).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        for consent in BenchmarkConsentRecord.objects(case_id=str(case.id), consent_type=BENCHMARK_CONSENT_TYPE, status="active"):
            consent.status = "revoked"
            consent.revoked_by = str(user.id)
            consent.revoked_at = datetime.now()
            consent.updated_at = datetime.now()
            consent.save()
        case.benchmark_consent = False
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Benchmark consent revoked",
            payload={"benchmark_consent": AdvisoryService._benchmark_consent_state(case)},
        )

    @staticmethod
    def _active_benchmark_consent(case: AdvisoryCase):
        return BenchmarkConsentRecord.objects(
            case_id=str(case.id),
            user_id=case.user_id,
            consent_type=BENCHMARK_CONSENT_TYPE,
            status="active",
        ).order_by("-created_at").first()

    @staticmethod
    def _benchmark_consent_state(case: AdvisoryCase):
        active = AdvisoryService._active_benchmark_consent(case)
        if case.benchmark_consent != bool(active):
            case.benchmark_consent = bool(active)
            case.updated_at = datetime.now()
            case.save()
        return {
            "active": bool(active),
            "terms_version": active.terms_version if active else BENCHMARK_TERMS_VERSION,
            "terms_text": active.terms_text if active else BENCHMARK_TERMS_TEXT,
            "consent": active.to_dict() if active else None,
        }

    @staticmethod
    def answer_assistant_question(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        question = (data.question or "").strip()
        if not question:
            return 400, DataErrorSchema(code=400, message="Question is required")

        case = None
        if data.case_id:
            case = AdvisoryCase.objects(id=data.case_id).first()
            if not case:
                return 404, DataErrorSchema(code=404, message="Advisory case not found")

        try:
            limit = max(1, min(int(data.limit), 10))
        except (TypeError, ValueError):
            limit = 6

        retrieved_sources = (
            AdvisoryRetrievalService.retrieve_for_case(case, question, limit=limit)
            if case
            else AdvisoryRetrievalService.retrieve_global(question, limit=limit)
        )
        citations = retrieved_sources.get("citations", [])
        answer = AdvisoryService._controlled_answer_payload(question, citations, case)
        answer["cited_sources"] = retrieved_sources
        answer_log = AdvisoryService._log_assistant_answer(user, case, answer)
        answer["answer_log_id"] = str(answer_log.id)
        answer["answer_log"] = answer_log.to_dict()
        return 200, DataSuccessSchema(code=200, message="OK", payload={"answer": answer})

    @staticmethod
    def _log_assistant_answer(user, case, answer):
        log = AdvisoryAssistantAnswerLog(
            case_id=str(case.id) if case else "",
            user_id=case.user_id if case else "",
            asked_by=str(user.id),
            question=answer.get("question", ""),
            status=answer.get("status", ""),
            answer=answer.get("answer", ""),
            answer_bullets=list(answer.get("answer_bullets") or []),
            source_citations=list(answer.get("source_citations") or []),
            cited_sources=dict(answer.get("cited_sources") or {}),
            safety_flags=list(answer.get("safety_flags") or []),
            assumptions_and_limits=list(answer.get("assumptions_and_limits") or []),
        )
        log.save()
        return log

    @staticmethod
    def _controlled_answer_payload(question: str, citations, case):
        bullets = []
        for citation in citations[:4]:
            snippet = citation.get("source_snippet") or citation.get("snippet") or "Review the cited source before using this answer."
            bullets.append(f"{citation.get('title', 'Source')}: {snippet}")

        if not bullets:
            bullets = ["No indexed Teramina source matched strongly enough. Add or reindex source material before using this answer."]

        disease_terms = ["disease", "wssv", "ehp", "ahpnd", "ems", "imnv", "vibrio", "mortality"]
        safety_flags = []
        if any(term in question.lower() for term in disease_terms):
            safety_flags.append("Disease-related guidance requires lab data and expert review before client use.")

        return {
            "status": "source_cited_internal_draft",
            "case_id": str(case.id) if case else "",
            "question": question,
            "answer": "This internal answer is assembled only from indexed Teramina advisory sources. Review citations before use.",
            "answer_bullets": bullets,
            "source_citations": citations,
            "safety_flags": safety_flags,
            "assumptions_and_limits": [
                "Internal operator draft only.",
                "Use only with visible source citations.",
                "Do not treat this as disease diagnosis or production guarantee.",
                "Escalate high-stakes technical advice to expert review before client delivery.",
            ],
        }

    @staticmethod
    def get_case(case_id: str, user_id: str):
        case = AdvisoryCase.objects(id=case_id, user_id=user_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        report = AdvisoryReport.objects(id=case.report_id, user_id=user_id, status="delivered").first() if case.report_id else None
        expert_reviews = [
            review.to_dict()
            for review in AdvisoryExpertReview.objects(case_id=case_id, user_id=user_id, status="delivered").order_by("-created_at")
        ]
        retainer_cadences = [
            cadence.to_dict()
            for cadence in RetainerCadence.objects(case_id=case_id, user_id=user_id).order_by("next_review_at", "-created_at")
        ]
        hatcheries = [
            profile.to_dict()
            for profile in HatcheryProfile.objects(case_id=case_id, user_id=user_id, client_visible=True).order_by("-created_at")
        ]
        hatchery_records = [
            record.to_dict()
            for record in HatcheryOperationalRecord.objects(case_id=case_id, user_id=user_id, client_visible=True).order_by("-record_date", "-created_at")
        ]
        investor_scores = [
            score.to_dict()
            for score in InvestorDueDiligenceScore.objects(case_id=case_id, user_id=user_id, client_visible=True).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "case": case.to_dict(),
                "report": report.to_dict() if report else None,
                "expert_reviews": expert_reviews,
                "retainer_cadences": retainer_cadences,
                "hatchery_profiles": hatcheries,
                "hatchery_records": hatchery_records,
                "investor_scores": investor_scores,
                "benchmark_consent": AdvisoryService._benchmark_consent_state(case),
            },
        )

    @staticmethod
    def add_case_file(user, case_id: str, data):
        case = AdvisoryCase.objects(id=case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if not _can_access_case(user, case):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        file_data = AdvisoryService._normalize_case_file(data.dict(), case, str(user.id))
        case.uploaded_files = list(case.uploaded_files or []) + [file_data]
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(code=200, message="Advisory file attached", payload={"case": case.to_dict(include_private=_is_admin(user))})

    @staticmethod
    def upload_case_file(user, case_id: str, file, description: str = ""):
        case = AdvisoryCase.objects(id=case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if not _can_access_case(user, case):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        original_name = os.path.basename(file.name)
        storage_name = f"advisory/{case.user_id}/{case_id}/{uuid4().hex}-{original_name}"
        saved_name = default_storage.save(storage_name, ContentFile(file.read()))
        file_data = AdvisoryService._normalize_case_file(
            {
                "name": original_name,
                "url": default_storage.url(saved_name),
                "content_type": file.content_type,
                "description": description,
            },
            case,
            str(user.id),
        )
        case.uploaded_files = list(case.uploaded_files or []) + [file_data]
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Advisory file uploaded",
            payload={"case": case.to_dict(include_private=_is_admin(user))},
        )

    @staticmethod
    def _normalize_case_file(file_ref, case: AdvisoryCase, uploaded_by: str):
        return {
            "file_id": file_ref.get("file_id") or f"case-file-{uuid4().hex}",
            "case_id": str(case.id),
            "user_id": case.user_id,
            "name": file_ref.get("name", ""),
            "url": file_ref.get("url", ""),
            "content_type": file_ref.get("content_type", ""),
            "description": file_ref.get("description", ""),
            "access_scope": "case_private",
            "uploaded_by": uploaded_by,
            "uploaded_at": file_ref.get("uploaded_at") or datetime.now().isoformat(),
        }

    @staticmethod
    def update_case(user, case_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        case = AdvisoryCase.objects(id=case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        updates = data.dict(exclude_unset=True)
        for key, value in updates.items():
            setattr(case, key, value or "")
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(code=200, message="Advisory case updated", payload={"case": case.to_dict(include_private=True)})

    @staticmethod
    def build_assistant_brief(user, case_id: str):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        case = AdvisoryCase.objects(id=case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        expert_reviews = [
            review.to_dict(include_private=True)
            for review in AdvisoryExpertReview.objects(case_id=case_id).order_by("-created_at")
        ]
        reports = [
            report.to_dict(include_private=True)
            for report in AdvisoryReport.objects(case_id=case_id).order_by("-created_at")
        ]
        cadences = [
            cadence.to_dict(include_private=True)
            for cadence in RetainerCadence.objects(case_id=case_id).order_by("next_review_at", "-created_at")
        ]
        hatcheries = [
            profile.to_dict(include_private=True)
            for profile in HatcheryProfile.objects(case_id=case_id).order_by("-created_at")
        ]
        hatchery_records = [
            record.to_dict(include_private=True)
            for record in HatcheryOperationalRecord.objects(case_id=case_id).order_by("-record_date", "-created_at")
        ]
        investor_scores = [
            score.to_dict(include_private=True)
            for score in InvestorDueDiligenceScore.objects(case_id=case_id).order_by("-created_at")
        ]
        brief = AdvisoryService._build_brief_payload(
            case,
            expert_reviews,
            reports,
            cadences,
            hatcheries,
            hatchery_records,
            investor_scores,
        )
        brief_log = AdvisoryService._log_assistant_brief(user, case, brief)
        brief["brief_log_id"] = str(brief_log.id)
        brief["brief_log"] = brief_log.to_dict()
        return 200, DataSuccessSchema(code=200, message="OK", payload={"brief": brief})

    @staticmethod
    def accept_assistant_brief(user, log_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        brief_log = AdvisoryAssistantBriefLog.objects(id=log_id).first()
        if not brief_log:
            return 404, DataErrorSchema(code=404, message="Assistant brief log not found")

        brief_log.status = "accepted"
        brief_log.accepted_by = str(user.id)
        brief_log.accepted_report_id = data.report_id or ""
        brief_log.accepted_at = datetime.now()
        brief_log.updated_at = datetime.now()
        brief_log.save()
        return 200, DataSuccessSchema(code=200, message="Assistant brief accepted", payload={"brief_log": brief_log.to_dict()})

    @staticmethod
    def _log_assistant_brief(user, case: AdvisoryCase, brief):
        draft_report = dict(brief.get("draft_report") or {})
        cited_sources = dict(brief.get("cited_sources") or {})
        brief_log = AdvisoryAssistantBriefLog(
            case_id=str(case.id),
            user_id=case.user_id,
            generated_by=str(user.id),
            query=cited_sources.get("query", ""),
            missing_data=list(brief.get("missing_data") or []),
            source_citations=list(draft_report.get("source_citations") or []),
            draft_report=draft_report,
        )
        brief_log.save()
        return brief_log

    @staticmethod
    def create_report_from_assistant_brief(user, log_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        brief_log = AdvisoryAssistantBriefLog.objects(id=log_id).first()
        if not brief_log:
            return 404, DataErrorSchema(code=404, message="Assistant brief log not found")
        case = AdvisoryCase.objects(id=brief_log.case_id, user_id=brief_log.user_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")
        if data.status not in ["draft", "expert_review_required"]:
            return 400, DataErrorSchema(code=400, message="Assistant draft reports cannot be delivered without expert review")

        existing_report = AdvisoryReport.objects(id=brief_log.accepted_report_id).first() if brief_log.accepted_report_id else None
        if existing_report:
            return 200, DataSuccessSchema(
                code=200,
                message="Assistant draft report already exists",
                payload={"report": existing_report.to_dict(include_private=True), "brief_log": brief_log.to_dict()},
            )

        draft_report = dict(brief_log.draft_report or {})
        report = AdvisoryReport(
            case_id=brief_log.case_id,
            user_id=brief_log.user_id,
            title=draft_report.get("title") or "Assistant Draft Report",
            executive_summary=draft_report.get("executive_summary", ""),
            data_received=draft_report.get("data_received", []),
            key_findings=draft_report.get("key_findings", []),
            likely_causes=draft_report.get("likely_causes", []),
            technical_interpretation=draft_report.get("technical_interpretation", ""),
            economic_implication=draft_report.get("economic_implication", ""),
            corrective_action_plan=draft_report.get("corrective_action_plan", []),
            monitoring_plan=draft_report.get("monitoring_plan", []),
            assumptions_and_limits=draft_report.get("assumptions_and_limits", []),
            source_citations=list(brief_log.source_citations or []),
            generated_from_brief_log_id=str(brief_log.id),
            status=data.status,
        )
        report.save()
        brief_log.status = "accepted"
        brief_log.accepted_by = str(user.id)
        brief_log.accepted_report_id = str(report.id)
        brief_log.accepted_at = datetime.now()
        brief_log.updated_at = datetime.now()
        brief_log.save()
        case.report_id = str(report.id)
        case.status = "in_review"
        case.updated_at = datetime.now()
        case.save()
        AdvisoryService._log_report_workflow_event(
            report,
            previous_status="",
            new_status=report.status,
            review_note=f"Created from assistant brief log {str(brief_log.id)}.",
            changed_by=str(user.id),
        )
        return 200, DataSuccessSchema(
            code=200,
            message="Assistant draft report created",
            payload={"report": report.to_dict(include_private=True), "brief_log": brief_log.to_dict()},
        )

    @staticmethod
    def _build_brief_payload(case: AdvisoryCase, expert_reviews, reports, cadences, hatcheries=None, hatchery_records=None, investor_scores=None):
        hatcheries = hatcheries or []
        hatchery_records = hatchery_records or []
        investor_scores = investor_scores or []
        intake = dict(case.intake_data or {})
        main_question = intake.get(CASE_MAIN_QUESTION_KEYS.get(case.case_type, "main_problem")) or intake.get("main_problem") or ""
        required_keys = CASE_REQUIRED_INTAKE.get(case.case_type, [])
        missing_data = [_humanize_key(key) for key in required_keys if not _has_value(intake.get(key))]
        intake_summary = [
            {"key": key, "label": _humanize_key(key), "value": _short_value(value)}
            for key, value in intake.items()
            if _has_value(value)
        ]
        file_names = [file_ref.get("name", "Attached file") for file_ref in case.uploaded_files or []]
        uploaded_file_checks = AdvisoryService._uploaded_file_isolation_checks(case)
        expert_findings = [
            finding
            for review in expert_reviews
            for finding in review.get("findings", [])
            if finding
        ]
        risk_flags = [
            flag
            for review in expert_reviews
            for flag in review.get("risk_flags", [])
            if flag
        ]
        next_actions = [
            action
            for review in expert_reviews
            for action in review.get("next_actions", [])
            if action
        ]
        data_received = [_humanize_key(item["key"]) for item in intake_summary]
        data_received.extend([f"File: {name}" for name in file_names])
        if case.farm_id:
            data_received.append(f"Linked farm ID: {case.farm_id}")
        if case.pond_id:
            data_received.append(f"Linked pond ID: {case.pond_id}")
        if case.cycle_id:
            data_received.append(f"Linked cycle ID: {case.cycle_id}")
        if hatcheries:
            data_received.append(f"Hatchery profiles: {len(hatcheries)}")
        if hatchery_records:
            data_received.append(f"Hatchery operational records: {len(hatchery_records)}")
        if investor_scores:
            latest_score = investor_scores[0]
            data_received.append(f"Investor due-diligence score: {latest_score.get('overall_score')} ({latest_score.get('risk_level')})")

        source_query = AdvisoryService._retrieval_query_for_case(case, intake_summary, main_question)
        retrieved_sources = AdvisoryRetrievalService.retrieve_for_case(case, source_query, limit=6)
        citations = retrieved_sources.get("citations", [])
        reference_documents = [
            source
            for source in citations
            if source.get("source_kind") == "content_item"
        ]
        if not reference_documents:
            reference_documents = AdvisoryService._reference_documents_for_case(case)

        case_type_label = case.case_type.replace("_", " ")
        findings = []
        if main_question:
            findings.append(f"Client question: {main_question}")
        findings.append(f"Case is currently in {case.status} status.")
        if expert_findings:
            findings.extend(expert_findings[:5])
        else:
            findings.append("No structured expert findings have been delivered yet.")
        if hatchery_records:
            record_types = sorted({record.get("record_type", "") for record in hatchery_records if record.get("record_type")})
            findings.append(f"Linked hatchery records available: {', '.join(record_types)}.")
        if investor_scores:
            latest_score = investor_scores[0]
            findings.append(
                f"Latest investor due-diligence score is {latest_score.get('overall_score')} with {latest_score.get('risk_level')} risk."
            )

        corrective_actions = []
        if missing_data:
            corrective_actions.append(f"Request or verify missing data: {', '.join(missing_data[:6])}.")
        corrective_actions.extend(next_actions[:5])
        corrective_actions.append("Review the draft against raw farm, hatchery, or project records before client delivery.")

        draft_report = {
            "title": f"Assistant Draft: {case.title or case_type_label.title()}",
            "executive_summary": AdvisoryService._assistant_executive_summary(case, main_question),
            "data_received": data_received,
            "key_findings": findings,
            "likely_causes": risk_flags or ["Expert cause ranking is not available from the current structured data."],
            "corrective_action_plan": corrective_actions,
            "monitoring_plan": AdvisoryService._monitoring_plan_for_case(case.case_type),
            "assumptions_and_limits": [
                "This is an internal first-pass brief generated from Teramina records.",
                "It does not diagnose disease without laboratory evidence.",
                "It must be reviewed by a qualified expert before client delivery.",
                "Uploaded case documents are treated as case-private client records.",
            ],
            "source_citations": citations,
        }

        return {
            "case": case.to_dict(include_private=True),
            "intake_summary": intake_summary,
            "missing_data": missing_data,
            "reference_documents": reference_documents,
            "cited_sources": retrieved_sources,
            "uploaded_file_checks": uploaded_file_checks,
            "existing_reports": reports,
            "expert_reviews": expert_reviews,
            "retainer_cadences": cadences,
            "hatchery_profiles": hatcheries,
            "hatchery_records": hatchery_records,
            "investor_scores": investor_scores,
            "draft_report": draft_report,
        }

    @staticmethod
    def _uploaded_file_isolation_checks(case: AdvisoryCase):
        checks = []
        for file_ref in case.uploaded_files or []:
            issues = []
            if file_ref.get("case_id") != str(case.id):
                issues.append("case_id_mismatch")
            if file_ref.get("user_id") != case.user_id:
                issues.append("user_id_mismatch")
            if file_ref.get("access_scope") != "case_private":
                issues.append("access_scope_not_case_private")
            if not file_ref.get("name"):
                issues.append("missing_name")
            if not file_ref.get("url"):
                issues.append("missing_url")
            checks.append({
                "file_id": file_ref.get("file_id", ""),
                "name": file_ref.get("name", ""),
                "access_scope": file_ref.get("access_scope", ""),
                "status": "needs_review" if issues else "passed",
                "issues": issues,
            })
        return {
            "total_files": len(checks),
            "passed": len([check for check in checks if check["status"] == "passed"]),
            "needs_review": len([check for check in checks if check["status"] == "needs_review"]),
            "checks": checks,
        }

    @staticmethod
    def _retrieval_query_for_case(case: AdvisoryCase, intake_summary, main_question: str):
        values = [
            case.title,
            case.case_type.replace("_", " "),
            main_question,
            " ".join(item["value"] for item in intake_summary[:8]),
        ]
        return " ".join(value for value in values if value)

    @staticmethod
    def _assistant_executive_summary(case: AdvisoryCase, main_question: str) -> str:
        case_type_label = case.case_type.replace("_", " ")
        if main_question:
            return (
                f"{case.title or case_type_label.title()} is a {case_type_label} case focused on: {main_question}. "
                "The available intake should be checked against linked operational data, attached files, and expert review notes before delivery."
            )
        return (
            f"{case.title or case_type_label.title()} is a {case_type_label} case. "
            "The available intake is incomplete, so the next step is to confirm missing data before technical interpretation."
        )

    @staticmethod
    def _monitoring_plan_for_case(case_type: str):
        if case_type == "hatchery_review":
            return ["Track mating, spawning, hatching, nauplii output, PL quality, and disease test cadence."]
        if case_type == "investor_due_diligence":
            return ["Track capex, opex, production assumptions, management risks, and ROI sensitivity."]
        if case_type == "procurement_advisory":
            return ["Track supplier fit, biosecurity evidence, genetic trait fit, delivery timeline, and receiving SOP compliance."]
        if case_type == "retainer":
            return ["Track agreed cadence, open action items, latest KPIs, data gaps, and management decisions."]
        return ["Track feed, water quality, sampling, mortality, disease tests, harvest result, and economic impact."]

    @staticmethod
    def _reference_documents_for_case(case: AdvisoryCase):
        categories = CASE_REFERENCE_CATEGORIES.get(case.case_type, set())
        case_terms = set(case.case_type.split("_"))
        scored = []
        for item in ContentItem.objects(status="published").order_by("-published_at", "title")[:100]:
            score = 0
            if item.category in categories:
                score += 3
            searchable = " ".join([item.title, item.summary, item.category, " ".join(item.tags or [])]).lower()
            score += sum(1 for term in case_terms if term in searchable)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].title))
        return [
            {
                "id": str(item.id),
                "title": item.title,
                "slug": item.slug,
                "category": item.category,
                "content_type": item.content_type,
                "access_level": item.access_level,
                "language": item.language,
                "variant_type": item.variant_type,
                "summary": item.summary,
            }
            for _, item in scored[:5]
        ]

    @staticmethod
    def admin_list_expert_reviews(user, status=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status
        reviews = [
            review.to_dict(include_private=True)
            for review in AdvisoryExpertReview.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"reviews": reviews})

    @staticmethod
    def create_expert_review(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        case = AdvisoryCase.objects(id=data.case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        review = AdvisoryExpertReview(
            case_id=data.case_id,
            user_id=case.user_id,
            reviewer_id=str(user.id),
            review_type=data.review_type,
            summary=data.summary,
            findings=data.findings or [],
            recommendations=data.recommendations or [],
            risk_flags=data.risk_flags or [],
            next_actions=data.next_actions or [],
            status=data.status,
            delivered_at=datetime.now() if data.status == "delivered" else None,
        )
        review.save()
        case.status = "in_review" if case.status == "inquiry" else case.status
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(code=200, message="Expert review created", payload={"review": review.to_dict(include_private=True)})

    @staticmethod
    def admin_list_retainer_cadences(user, status=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status
        cadences = [
            cadence.to_dict(include_private=True)
            for cadence in RetainerCadence.objects(**query).order_by("next_review_at", "-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"cadences": cadences})

    @staticmethod
    def create_retainer_cadence(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        case = AdvisoryCase.objects(id=data.case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        cadence = RetainerCadence(
            case_id=data.case_id,
            user_id=case.user_id,
            cadence_type=data.cadence_type,
            status=data.status,
            last_review_at=data.last_review_at,
            next_review_at=data.next_review_at,
            agenda=data.agenda or [],
            notes=data.notes,
            created_by=str(user.id),
        )
        cadence.save()
        case.updated_at = datetime.now()
        case.save()
        return 200, DataSuccessSchema(code=200, message="Retainer cadence created", payload={"cadence": cadence.to_dict(include_private=True)})

    @staticmethod
    def admin_list_reports(user, status=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status

        reports = [
            report.to_dict(include_private=True)
            for report in AdvisoryReport.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"reports": reports})

    @staticmethod
    def update_report_workflow(user, report_id: str, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        if data.status not in AdvisoryService.REPORT_STATUSES:
            return 400, DataErrorSchema(code=400, message="Invalid report status")
        report = AdvisoryReport.objects(id=report_id).first()
        if not report:
            return 404, DataErrorSchema(code=404, message="Advisory report not found")
        case = AdvisoryCase.objects(id=report.case_id, user_id=report.user_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        previous_status = report.status
        report.status = data.status
        report.review_note = data.review_note or ""
        report.reviewed_by = str(user.id)
        report.reviewed_at = datetime.now()
        report.updated_at = datetime.now()
        report.delivered_at = datetime.now() if data.status == "delivered" else None
        report.save()

        case.report_id = str(report.id)
        case.status = "report_ready" if data.status == "delivered" else "in_review"
        case.updated_at = datetime.now()
        case.save()
        if report.status == "delivered":
            AdvisoryRetrievalService.index_report(report, case)
        AdvisoryService._log_report_workflow_event(
            report,
            previous_status=previous_status,
            new_status=report.status,
            review_note=report.review_note,
            changed_by=str(user.id),
        )

        return 200, DataSuccessSchema(
            code=200,
            message="Advisory report workflow updated",
            payload={"report": report.to_dict(include_private=True), "case": case.to_dict(include_private=True)},
        )

    @staticmethod
    def create_report(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        case = AdvisoryCase.objects(id=data.case_id).first()
        if not case:
            return 404, DataErrorSchema(code=404, message="Advisory case not found")

        report = AdvisoryReport(
            case_id=data.case_id,
            user_id=case.user_id,
            title=data.title,
            executive_summary=data.executive_summary,
            data_received=data.data_received or [],
            key_findings=data.key_findings or [],
            likely_causes=data.likely_causes or [],
            technical_interpretation=data.technical_interpretation,
            economic_implication=data.economic_implication,
            corrective_action_plan=data.corrective_action_plan or [],
            monitoring_plan=data.monitoring_plan or [],
            assumptions_and_limits=data.assumptions_and_limits or [],
            source_citations=data.source_citations or [],
            generated_from_brief_log_id=data.generated_from_brief_log_id,
            file_url=data.file_url,
            status=data.status,
            delivered_at=datetime.now() if data.status == "delivered" else None,
        )
        report.save()
        case.report_id = str(report.id)
        if report.status == "delivered":
            case.status = "report_ready"
        case.updated_at = datetime.now()
        case.save()
        AdvisoryService._log_report_workflow_event(
            report,
            previous_status="",
            new_status=report.status,
            review_note="Report created manually.",
            changed_by=str(user.id),
        )
        return 200, DataSuccessSchema(code=200, message="Advisory report created", payload={"report": report.to_dict()})

    @staticmethod
    def _log_report_workflow_event(report: AdvisoryReport, previous_status: str, new_status: str, review_note: str, changed_by: str):
        AdvisoryReportWorkflowEvent(
            report_id=str(report.id),
            case_id=report.case_id,
            user_id=report.user_id,
            previous_status=previous_status or "",
            new_status=new_status,
            review_note=review_note or "",
            changed_by=changed_by,
        ).save()

    @staticmethod
    def get_report(report_id: str, user_id: str):
        report = AdvisoryReport.objects(id=report_id, user_id=user_id, status="delivered").first()
        if not report:
            return 404, DataErrorSchema(code=404, message="Advisory report not found")
        return 200, DataSuccessSchema(code=200, message="OK", payload={"report": report.to_dict()})
