from datetime import datetime
from uuid import uuid4

from mongoengine.errors import NotUniqueError, ValidationError

from teramina.content.models.content_model import ContentItem
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.advisory_model import (
    AdvisoryAssistantBriefLog,
    AdvisoryCase,
    AdvisoryExpertReview,
    AdvisoryReport,
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
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "case": case.to_dict(),
                "report": report.to_dict() if report else None,
                "expert_reviews": expert_reviews,
                "retainer_cadences": retainer_cadences,
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
        brief = AdvisoryService._build_brief_payload(case, expert_reviews, reports, cadences)
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
        return 200, DataSuccessSchema(
            code=200,
            message="Assistant draft report created",
            payload={"report": report.to_dict(include_private=True), "brief_log": brief_log.to_dict()},
        )

    @staticmethod
    def _build_brief_payload(case: AdvisoryCase, expert_reviews, reports, cadences):
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
        return 200, DataSuccessSchema(code=200, message="Advisory report created", payload={"report": report.to_dict()})

    @staticmethod
    def get_report(report_id: str, user_id: str):
        report = AdvisoryReport.objects(id=report_id, user_id=user_id, status="delivered").first()
        if not report:
            return 404, DataErrorSchema(code=404, message="Advisory report not found")
        return 200, DataSuccessSchema(code=200, message="OK", payload={"report": report.to_dict()})
