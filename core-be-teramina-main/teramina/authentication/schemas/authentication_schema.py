# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema
from pydantic import ConfigDict


class FirebaseTokenSchema(Schema):
    token: str


class UserLoginSchema(Schema):
    email: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "title": "Login",
            "example": {"email": "sukoco@gmail.com", "password": "Password123!"},
        }
    )
