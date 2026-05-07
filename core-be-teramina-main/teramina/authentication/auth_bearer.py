# pylint: disable=too-few-public-methods, W0613, R0801

import os
from datetime import datetime, timezone, timedelta
from ninja.security import HttpBearer
import jwt
from jwt.exceptions import (
    InvalidAudienceError,
    InvalidAlgorithmError,
    DecodeError,
    InvalidTokenError,
)
from ..user.models.user_model import User


class AuthBearer(HttpBearer):
    """Django ninja HTTP bearer extender"""

    def authenticate(self, request, token):
        """authentication"""
        try:
            secret_key = os.getenv("JWT_SECRET_KEY")
            jwt_payload = jwt.decode(
                token, secret_key, algorithms=["HS256"]
            )
            if jwt_payload["exp"] < datetime.now(timezone.utc).timestamp():
                return False

            if User.objects(id=jwt_payload["data"]["id"]).only("id").first():
                return token
        except (
            InvalidAudienceError,
            InvalidAlgorithmError,
            DecodeError,
            InvalidTokenError,
        ):
            return False

        return None

    def authenticate_with_refresh_token(self, request, token):
        """authentication returned token & refresh tokens"""
        try:
            secret_key = os.getenv("JWT_SECRET_KEY")
            jwt_payload = jwt.decode(
                token, secret_key, algorithms=["HS256"]
            )
            if jwt_payload["exp"] < datetime.now(timezone.utc).timestamp():
                return False

            user = (
                User.objects(id=jwt_payload["data"]["id"]).only("id", "email").first()
            )
            if not user:
                return False
            jwt_payload = {
                "exp": datetime.now(timezone.utc) + timedelta(minutes=120),
                "iat": datetime.now(timezone.utc),
                "data": {"id": str(user.id), "email": user.email, "name": user.name},
            }

            jwt_token = jwt.encode(
                jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
            )

            refresh_payload = {
                "exp": datetime.now(timezone.utc) + timedelta(days=7), 
                "iat": datetime.now(timezone.utc),
                "data": {"id": str(user.id), "email": user.email, "name": user.name},
            }
            refresh_token = jwt.encode(
                refresh_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
            )
            return {"token": jwt_token, "refresh_token": refresh_token}
        except (
            InvalidAudienceError,
            InvalidAlgorithmError,
            DecodeError,
            InvalidTokenError,
        ):
            return False

    def authenticate_returned_email(self, request, token):
        """authentication returned email"""
        try:
            secret_key = os.getenv("JWT_SECRET_KEY")
            jwt_payload = jwt.decode(
                token, secret_key, algorithms=["HS256"]
            )
            if jwt_payload["exp"] < datetime.now(timezone.utc).timestamp():
                return False

            user = (
                User.objects(id=jwt_payload["data"]["id"]).only("id", "email").first()
            )
            if user:
                return (user.email, str(user.id))
        except (
            InvalidAudienceError,
            InvalidAlgorithmError,
            DecodeError,
            InvalidTokenError,
        ):
            return False

        return None
