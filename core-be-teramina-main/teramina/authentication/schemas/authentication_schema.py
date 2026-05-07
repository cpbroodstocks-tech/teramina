# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class SignedUserSchema(Schema):
    email: str
    photoURL: str
    displayName: str


class UserLoginSchema(Schema):
    email: str
    password: str

    class Config:
        schema_extra = {
            "title": "Login",
            "example": {"email": "sukoco@gmail.com", "password": "Password123!"},
        }
