# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from ..schemas.authentication_schema import UserLoginSchema, SignedUserSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..services.authentication_service import user_login
from ..services.google_authentication_service import (
    signed_user,
    signed_token_using_firebase,
    is_active,
    signed_with_refresh_token
)

router = Router(tags=["Authentication"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/login", response=response_schema)
def user_login_endpoint(request, data: UserLoginSchema = Body(...)):
    return user_login(data)


@router.post("/verify-user", response=response_schema)
def user_signed(request, data: SignedUserSchema = Body(...)):
    return signed_user(data)


@router.post("/firebase-verify-user", response=response_schema)
def user_signed_using_firebase(request, token):
    return signed_token_using_firebase(token)


@router.get("/verify-user-by-token", response=response_schema)
def user_active_checker(request, token):
    return is_active(request, token)

@router.get("/verify-with-refresh-token", response=response_schema)
def user_signed_with_refresh_token(request):
    token = request.META.get("HTTP_AUTHORIZATION", " ").split(" ")[-1]
    return signed_with_refresh_token(request, token)
