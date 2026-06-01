from django.http import HttpResponse
from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.content_schema import (
    ContentAccessGrantSchema,
    ContentItemSchema,
    ContentItemUpdateSchema,
    ContentWorkflowTransitionSchema,
)
from ..services.content_service import ContentService
from ..services.content_pdf_service import build_content_pdf

router = Router(tags=["Content"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema, 404: DataErrorSchema}


@router.get("/items", response=response_schema)
def list_content(request, category: str = "", tag: str = "", content_type: str = "",
                 language: str = "", access_level: str = "", variant_group_id: str = "", variant_type: str = ""):
    return ContentService.list_items(
        category=category,
        tag=tag,
        content_type=content_type,
        language=language,
        access_level=access_level,
        variant_group_id=variant_group_id,
        variant_type=variant_type,
    )


@router.get("/items/{slug}/pdf")
def download_public_content_pdf(request, slug: str):
    code, result = ContentService.get_downloadable_item(slug)
    if code != 200:
        return HttpResponse(result.message, status=code)
    pdf_bytes = build_content_pdf(result)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{result.slug}.pdf"'
    return response


@router.get("/items/{slug}", response=response_schema)
def get_content(request, slug: str):
    return ContentService.get_item(slug)


@router.get("/my-items", response=response_schema, auth=AuthBearer())
def list_my_content(request, category: str = "", tag: str = "", content_type: str = "",
                    language: str = "", access_level: str = "", variant_group_id: str = "", variant_type: str = ""):
    user = get_signed_in_user(request)
    return ContentService.list_items(
        user_id=str(user.id),
        category=category,
        tag=tag,
        content_type=content_type,
        language=language,
        access_level=access_level,
        variant_group_id=variant_group_id,
        variant_type=variant_type,
    )


@router.get("/my-items/{slug}/pdf", auth=AuthBearer())
def download_my_content_pdf(request, slug: str):
    user = get_signed_in_user(request)
    code, result = ContentService.get_downloadable_item(slug, user_id=str(user.id))
    if code != 200:
        return HttpResponse(result.message, status=code)
    pdf_bytes = build_content_pdf(result)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{result.slug}.pdf"'
    return response


@router.get("/my-items/{slug}", response=response_schema, auth=AuthBearer())
def get_my_content(request, slug: str):
    user = get_signed_in_user(request)
    return ContentService.get_item(slug, user_id=str(user.id))


@router.get("/admin/items", response=response_schema, auth=AuthBearer())
def admin_list_content(request, status: str = "", access_level: str = "", language: str = "",
                       variant_group_id: str = "", variant_type: str = ""):
    user = get_signed_in_user(request)
    return ContentService.admin_list_items(
        user,
        status=status,
        access_level=access_level,
        language=language,
        variant_group_id=variant_group_id,
        variant_type=variant_type,
    )


@router.get("/admin/access", response=response_schema, auth=AuthBearer())
def admin_list_content_access(request, user_id: str = "", content_id: str = ""):
    user = get_signed_in_user(request)
    return ContentService.admin_list_access(user, user_id=user_id, content_id=content_id)


@router.get("/admin/items/{content_id}/revisions", response=response_schema, auth=AuthBearer())
def admin_list_content_revisions(request, content_id: str):
    user = get_signed_in_user(request)
    return ContentService.admin_list_revisions(user, content_id)


@router.get("/admin/items/{content_id}", response=response_schema, auth=AuthBearer())
def admin_get_content(request, content_id: str):
    user = get_signed_in_user(request)
    return ContentService.admin_get_item(user, content_id)


@router.post("/items", response=response_schema, auth=AuthBearer())
def create_content(request, data: ContentItemSchema = Body(...)):
    user = get_signed_in_user(request)
    return ContentService.create_item(user, data)


@router.patch("/items/{content_id}", response=response_schema, auth=AuthBearer())
def update_content(request, content_id: str, data: ContentItemUpdateSchema = Body(...)):
    user = get_signed_in_user(request)
    return ContentService.update_item(user, content_id, data)


@router.post("/items/{content_id}/workflow", response=response_schema, auth=AuthBearer())
def transition_content_workflow(request, content_id: str, data: ContentWorkflowTransitionSchema = Body(...)):
    user = get_signed_in_user(request)
    return ContentService.transition_workflow(user, content_id, data)


@router.post("/access", response=response_schema, auth=AuthBearer())
def grant_content_access(request, data: ContentAccessGrantSchema = Body(...)):
    user = get_signed_in_user(request)
    return ContentService.grant_access(user, data)
