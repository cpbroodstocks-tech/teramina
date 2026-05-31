from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.advisory_schema import (
    AdvisoryAssistantBriefAcceptSchema,
    AdvisoryAssistantDraftReportSchema,
    AdvisoryCaseCreateSchema,
    AdvisoryCaseFileSchema,
    AdvisoryCaseUpdateSchema,
    AdvisoryExpertReviewSchema,
    AdvisoryReportSchema,
    AdvisoryReportWorkflowSchema,
    RetainerCadenceSchema,
    ServicePackageSchema,
)
from ..services.advisory_service import AdvisoryService

router = Router(tags=["Advisory"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema, 404: DataErrorSchema}


@router.get("/packages", response=response_schema)
def list_packages(request):
    return AdvisoryService.list_packages()


@router.get("/packages/{slug}", response=response_schema)
def get_package(request, slug: str):
    return AdvisoryService.get_package(slug)


@router.post("/packages", response=response_schema, auth=AuthBearer())
def create_package(request, data: ServicePackageSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_package(user, data)


@router.post("/cases", response=response_schema, auth=AuthBearer())
def create_case(request, data: AdvisoryCaseCreateSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_case(str(user.id), data)


@router.get("/cases", response=response_schema, auth=AuthBearer())
def list_cases(request):
    user = get_signed_in_user(request)
    return AdvisoryService.list_cases(str(user.id))


@router.get("/history", response=response_schema, auth=AuthBearer())
def list_history(request, farm_id: str = "", pond_id: str = "", cycle_id: str = "", limit: int = 50):
    user = get_signed_in_user(request)
    return AdvisoryService.list_history(user, farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, limit=limit)


@router.get("/admin/cases", response=response_schema, auth=AuthBearer())
def admin_list_cases(request, status: str = "", case_type: str = ""):
    user = get_signed_in_user(request)
    return AdvisoryService.admin_list_cases(user, status=status, case_type=case_type)


@router.get("/admin/cases/{case_id}/assistant-brief", response=response_schema, auth=AuthBearer())
def build_assistant_brief(request, case_id: str):
    user = get_signed_in_user(request)
    return AdvisoryService.build_assistant_brief(user, case_id)


@router.post("/admin/assistant-brief-logs/{log_id}/accept", response=response_schema, auth=AuthBearer())
def accept_assistant_brief(request, log_id: str, data: AdvisoryAssistantBriefAcceptSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.accept_assistant_brief(user, log_id, data)


@router.post("/admin/assistant-brief-logs/{log_id}/draft-report", response=response_schema, auth=AuthBearer())
def create_report_from_assistant_brief(request, log_id: str, data: AdvisoryAssistantDraftReportSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_report_from_assistant_brief(user, log_id, data)


@router.post("/cases/{case_id}/files", response=response_schema, auth=AuthBearer())
def add_case_file(request, case_id: str, data: AdvisoryCaseFileSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.add_case_file(user, case_id, data)


@router.get("/cases/{case_id}", response=response_schema, auth=AuthBearer())
def get_case(request, case_id: str):
    user = get_signed_in_user(request)
    return AdvisoryService.get_case(case_id, str(user.id))


@router.patch("/cases/{case_id}", response=response_schema, auth=AuthBearer())
def update_case(request, case_id: str, data: AdvisoryCaseUpdateSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.update_case(user, case_id, data)


@router.post("/expert-reviews", response=response_schema, auth=AuthBearer())
def create_expert_review(request, data: AdvisoryExpertReviewSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_expert_review(user, data)


@router.get("/admin/expert-reviews", response=response_schema, auth=AuthBearer())
def admin_list_expert_reviews(request, status: str = ""):
    user = get_signed_in_user(request)
    return AdvisoryService.admin_list_expert_reviews(user, status=status)


@router.post("/retainer-cadences", response=response_schema, auth=AuthBearer())
def create_retainer_cadence(request, data: RetainerCadenceSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_retainer_cadence(user, data)


@router.get("/admin/retainer-cadences", response=response_schema, auth=AuthBearer())
def admin_list_retainer_cadences(request, status: str = ""):
    user = get_signed_in_user(request)
    return AdvisoryService.admin_list_retainer_cadences(user, status=status)


@router.post("/reports", response=response_schema, auth=AuthBearer())
def create_report(request, data: AdvisoryReportSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.create_report(user, data)


@router.get("/admin/reports", response=response_schema, auth=AuthBearer())
def admin_list_reports(request, status: str = ""):
    user = get_signed_in_user(request)
    return AdvisoryService.admin_list_reports(user, status=status)


@router.patch("/admin/reports/{report_id}/workflow", response=response_schema, auth=AuthBearer())
def update_report_workflow(request, report_id: str, data: AdvisoryReportWorkflowSchema = Body(...)):
    user = get_signed_in_user(request)
    return AdvisoryService.update_report_workflow(user, report_id, data)


@router.get("/reports/{report_id}", response=response_schema, auth=AuthBearer())
def get_report(request, report_id: str):
    user = get_signed_in_user(request)
    return AdvisoryService.get_report(report_id, str(user.id))
