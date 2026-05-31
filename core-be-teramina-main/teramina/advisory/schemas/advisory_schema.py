from datetime import datetime
from typing import Optional

from ninja import Schema


class ServicePackageSchema(Schema):
    name: str
    slug: str
    segment: str
    description: str = ""
    deliverables: list[str] = []
    required_data: list[str] = []
    price_min_idr: Optional[int] = None
    price_max_idr: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0


class AdvisoryCaseCreateSchema(Schema):
    service_package_id: Optional[str] = ""
    case_type: str
    farm_id: Optional[str] = ""
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""
    title: str = ""
    intake_data: dict = {}
    uploaded_files: list[dict] = []


class AdvisoryCaseUpdateSchema(Schema):
    status: Optional[str] = None
    farm_id: Optional[str] = None
    pond_id: Optional[str] = None
    cycle_id: Optional[str] = None
    expert_notes: Optional[str] = None
    report_id: Optional[str] = None


class AdvisoryReportSchema(Schema):
    case_id: str
    title: str
    executive_summary: str = ""
    data_received: list[str] = []
    key_findings: list[str] = []
    likely_causes: list[str] = []
    technical_interpretation: str = ""
    economic_implication: str = ""
    corrective_action_plan: list[str] = []
    monitoring_plan: list[str] = []
    assumptions_and_limits: list[str] = []
    source_citations: list[dict] = []
    generated_from_brief_log_id: str = ""
    file_url: str = ""
    status: str = "draft"


class AdvisoryCaseFileSchema(Schema):
    name: str
    url: str
    content_type: str = ""
    description: str = ""


class AdvisoryAssistantBriefAcceptSchema(Schema):
    report_id: str = ""


class AdvisoryAssistantDraftReportSchema(Schema):
    status: str = "expert_review_required"


class AdvisoryReportWorkflowSchema(Schema):
    status: str
    review_note: str = ""


class AdvisoryExpertReviewSchema(Schema):
    case_id: str
    review_type: str = "technical"
    summary: str = ""
    findings: list[str] = []
    recommendations: list[str] = []
    risk_flags: list[str] = []
    next_actions: list[str] = []
    status: str = "draft"


class RetainerCadenceSchema(Schema):
    case_id: str
    cadence_type: str = "monthly"
    status: str = "active"
    last_review_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    agenda: list[str] = []
    notes: str = ""
