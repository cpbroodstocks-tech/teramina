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
from ..schemas.authentication_schema import SignedUserSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ...helpers.default_data_updater import DataSeeder

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
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if not cred_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH env var not set")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "email": decoded_token["email"],
            "photoURL": decoded_token["picture"],
            "displayName": decoded_token["name"],
        }
    except InvalidIdTokenError as exc:
        raise ValueError("Could not verify token signature") from exc


def signed_user(data: SignedUserSchema):
    """signed user"""
    user = authenticate(data.email)

    try:
        if user is None:
            user = User(name=data.displayName, email=data.email, picture=data.photoURL)
            user.save()

        # verify_user(data.email)

        jwt_payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=120),
            "iat": datetime.now(timezone.utc),
            "data": {"id": str(user.id), "email": user.email, "name": user.name},
        }

        jwt_token = jwt.encode(
            jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        return 200, DataSuccessSchema(
            code=200, message="user verification success.", payload={"token": jwt_token}
        )
    except ValueError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))
    except AttributeError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))


def is_active(request, token):
    """is active user"""
    try:
        user = AuthBearer().authenticate_returned_email(request, token)
        status = bool(user)
        return 200, DataSuccessSchema(
            code=200,
            message="user verification success.",
            payload={"status": status, "email": user[0], "id": user[1]},
        )
    except (ValueError, TypeError) as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))
    except AttributeError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))

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
            data_seeder = DataSeeder(
                farm_id=os.getenv("SEEDER_FARM"),
                pond_id=os.getenv("SEEDER_POND"),
                cycle_id=os.getenv("SEEDER_CYCLE"),
                user_id=str(user.id),
            )
            data_seeder.set_data()

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
