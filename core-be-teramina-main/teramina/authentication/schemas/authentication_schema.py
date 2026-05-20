# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class FirebaseTokenSchema(Schema):
    token: str


class UserLoginSchema(Schema):
    email: str
    password: str

    class Config:
        schema_extra = {
            "title": "Login",
            "example": {"email": "sukoco@gmail.com", "password": "Password123!"},
        }
