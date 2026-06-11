# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body, File, Form
from ninja.files import UploadedFile

from ..schemas.profile_schema import (
    DemoExperienceEventSchema,
    DemoExperienceResetSchema,
    DemoExperienceUpdateSchema,
    FcmTokenSchema,
    UpdateProfileSchema,
)
from ..services.demo_experience_service import DemoExperienceService
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ...user.services.profile_service import ProfileService

from ...authentication.auth_bearer import AuthBearer
from ...authentication.services.authentication_service import get_signed_in_user
from ...helpers.file_validation import validate_image_file

router = Router(tags=["Profile"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/update-profile", response=response_schema, auth=AuthBearer())
def update_profile(
    request,
    data: UpdateProfileSchema = Form(...),
    file: UploadedFile = File(default=None),
):
    user = get_signed_in_user(request)
    if file is not None:
        file_error = validate_image_file(file)
        if file_error:
            return 400, DataErrorSchema(code=400, message=file_error)
    profile_service = ProfileService()
    return profile_service.update_profile(str(user.id), data, file)


@router.get("/get-profile", response=response_schema, auth=AuthBearer())
def profile(request):
    user = get_signed_in_user(request)
    profile_service = ProfileService()
    return profile_service.profile_info(str(user.id))


@router.get("/user-data-status", response=response_schema, auth=AuthBearer())
def data_status(request):
    user = get_signed_in_user(request)
    profile_service = ProfileService()
    return profile_service.is_there_data_status(user_id=str(user.id))


@router.post("/fcm-token", response=response_schema, auth=AuthBearer())
def update_fcm_token(request, data: FcmTokenSchema = Body(...)):
    """Store/update FCM token for push notifications."""
    user = get_signed_in_user(request)
    user.fcm_token = data.token
    user.save()
    return 200, DataSuccessSchema(code=200, message="Token updated", payload={})


@router.get("/demo-experience", response=response_schema, auth=AuthBearer())
def get_demo_experience(request):
    user = get_signed_in_user(request)
    return DemoExperienceService.get(str(user.id))


@router.post("/demo-experience/events", response=response_schema, auth=AuthBearer())
def record_demo_experience_event(request, data: DemoExperienceEventSchema = Body(...)):
    user = get_signed_in_user(request)
    return DemoExperienceService.record_event(str(user.id), data.event_name, data.properties)


@router.patch("/demo-experience", response=response_schema, auth=AuthBearer())
def update_demo_experience(request, data: DemoExperienceUpdateSchema = Body(...)):
    user = get_signed_in_user(request)
    return DemoExperienceService.update(str(user.id), data.checklist_dismissed)


@router.post("/demo-experience/reset", response=response_schema, auth=AuthBearer())
def reset_demo_experience(request, data: DemoExperienceResetSchema = Body(...)):
    user = get_signed_in_user(request)
    return DemoExperienceService.reset(str(user.id), data.confirmed)
