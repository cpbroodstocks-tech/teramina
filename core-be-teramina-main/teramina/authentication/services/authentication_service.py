import os
import logging
from datetime import datetime, timedelta, timezone
from mongoengine.errors import DoesNotExist
import jwt
from jwt.exceptions import DecodeError, InvalidTokenError
from django.contrib.auth.hashers import check_password
from ninja.errors import AuthenticationError

logger = logging.getLogger(__name__)

from ...user.models.user_model import User
from ..schemas.authentication_schema import UserLoginSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema


def authenticate(email, password):
    """user authentication based on email and password"""
    try:
        login_valid = User.objects(email=email).first()
        if not login_valid:
            return None
        pwd_valid = check_password(password, login_valid.password)

        if login_valid and pwd_valid:
            return User.objects(email=email).first()

        return None
    except DoesNotExist:
        return None


def user_login(data: UserLoginSchema):
    """login based function"""
    user = authenticate(data.email, data.password)
    if user is not None:
        jwt_payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=120),
            "iat": datetime.now(timezone.utc),
            "data": {"id": str(user.id), "email": user.email},
        }

        jwt_token = jwt.encode(
            jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        return 200, DataSuccessSchema(
            code=200, message="Login success.", payload={"token": jwt_token}
        )

    return 401, DataErrorSchema(code=401, message="Incorrect email or password.")


def _get_dev_user():
    """Return (or create) the dev user when DEV_BYPASS_TOKEN is active."""
    dev_email = "dev@teramina.local"
    user = User.objects(email=dev_email).first()
    if not user:
        user = User(name="Dev User", email=dev_email, role_user="admin")
        user.save()
    return user


def get_signed_in_user(request):
    """Get signed user data from the token.

    Raises AuthenticationError if the token is missing, malformed, invalid, or the
    user no longer exists. All callers are behind AuthBearer(), so this should only
    fail in edge cases (deleted user, key rotation, etc.).
    """
    from django.conf import settings
    dev_bypass = os.getenv("DEV_BYPASS_TOKEN")
    if dev_bypass and settings.DEBUG:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header == f"Bearer {dev_bypass}":
            return _get_dev_user()

    try:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationError()
        user_token = parts[1]
        decoded_token = jwt.decode(
            user_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"]
        )
        user = User.objects(id=decoded_token["data"]["id"]).first()
        if not user:
            raise AuthenticationError()
        return user
    except (DecodeError, InvalidTokenError, KeyError, IndexError) as exc:
        logger.warning("get_signed_in_user failed: %s", exc)
        raise AuthenticationError() from exc
