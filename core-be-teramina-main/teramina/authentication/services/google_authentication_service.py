import json
import logging
import os
from datetime import datetime, timedelta, timezone
import re
import jwt
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin._auth_utils import InvalidIdTokenError
from mongoengine.errors import DoesNotExist

from ..auth_bearer import AuthBearer
from ...user.models.user_model import User
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ...helpers.default_data_updater import DataSeeder

logger = logging.getLogger("teramina")

WHITE_LIST = [
    "anggoro.pras11@gmail.com",
    "hartono@uny.ac.id",
    "yzhang1.consultant@adb.org",
    "nghosh.contractor@adb.org",
    "aditya.mirzapahlevi@gmail.com",
    "cayurhaceum@gmail.com",
    "johnpatricksolano@gmail.com",
    "titinprihantini4@gmail.com",
    "bimagana23@gmail.com",
    "kenidaslt@gmail.com",
    "retnonuraini11@gmail.com",
]


def authenticate(email):
    """email authentication from Google's email"""
    try:
        login_valid = User.objects(email=email).only("email").first()
        if login_valid:
            return User.objects(email=email).only("email").first()

        return None
    except DoesNotExist:
        return None


def verify_user(email):
    """user verification"""
    if email in WHITE_LIST:
        return True

    allowed_domain = "teramina.io"
    try:
        pattern = r"(?<=@)\S+"
        domain = re.findall(pattern, email)
        if domain and (domain[0] == allowed_domain):
            return True

        raise ValueError
    except ValueError as exc:
        raise ValueError("Sorry, your email not allowed to sign in") from exc


def decode_token(token):
    """decoded token from firebase token"""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
        elif cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            raise ValueError("FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH env var not set")
        firebase_admin.initialize_app(cred)

    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "email": decoded_token["email"],
            "photoURL": decoded_token.get("picture", ""),
            "displayName": decoded_token.get("name") or decoded_token["email"].split("@")[0],
        }
    except InvalidIdTokenError as exc:
        raise ValueError("Could not verify token signature") from exc


def signed_with_refresh_token(request, token):
    """signed with refresh token"""
    try:
        user = AuthBearer().authenticate_with_refresh_token(request, token)
        return 200, DataSuccessSchema(
            code=200,
            message="user verification success.",
            payload=user
        )
    except (ValueError, TypeError) as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))
    except AttributeError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))


def signed_token_using_firebase(token):
    """signed token using firebase"""
    try:
        decoded_token = decode_token(token)
        user = authenticate(decoded_token["email"])

        if user is None:
            user = User(
                name=decoded_token["displayName"],
                email=decoded_token["email"],
                picture=decoded_token["photoURL"],
            )
            user.save()
            seeder_farm = os.getenv("SEEDER_FARM")
            seeder_pond = os.getenv("SEEDER_POND")
            seeder_cycle = os.getenv("SEEDER_CYCLE")
            if seeder_farm and seeder_pond and seeder_cycle:
                try:
                    data_seeder = DataSeeder(
                        farm_id=seeder_farm,
                        pond_id=seeder_pond,
                        cycle_id=seeder_cycle,
                        user_id=str(user.id),
                    )
                    data_seeder.set_data()
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning("Default data seeding skipped for user %s: %s", user.email, exc)

        jwt_payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=120),
            "iat": datetime.now(timezone.utc),
            "data": {"id": str(user.id), "email": user.email, "name": user.name},
        }

        jwt_token = jwt.encode(
            jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        # Refresh Token
        refresh_payload = {
            "exp": datetime.now(timezone.utc)
            + timedelta(days=7),  # Set the expiration time for the refresh token
            "iat": datetime.now(timezone.utc),
            "data": {"id": str(user.id), "email": user.email, "name": user.name},
        }
        refresh_token = jwt.encode(
            refresh_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        return 200, DataSuccessSchema(
            code=200,
            message="user verification success.",
            payload={"token": jwt_token, "refresh_token": refresh_token},
        )
    except ValueError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))
    except AttributeError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))
