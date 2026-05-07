# pylint: disable=missing-class-docstring, missing-function-docstring, too-few-public-methods

import re
from ninja import Schema
from pydantic import validator


class RegisterSchema(Schema):
    name: str
    email: str
    password: str
    phone: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Sundari Sukoco",
                "email": "sukoco@gmail.com",
                "password": "Password123!",
                "phone": "089563763889",
            }
        }

    @validator("email")
    @classmethod
    def validate_email(cls, value):
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        if not re.match(email_pattern, value):
            raise ValueError("invalid email format")

        return value

    @validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) <= 8:
            raise ValueError("password must be more than 8 characters")

        password_pattern = (
            r"^(?=.*[a-z])"
            r"(?=.*[A-Z])"
            r"(?=.*\d)"
            r"(?=.*[\!\@\#\$\%\&\*\+\-\=\?\.\,\:\;\'\"])"
            r"[A-Za-z\d\!\@\#\$\%\&\*\+\-\=\?\.\,\:\;\'\"]+$"
        )
        if not re.match(password_pattern, value):
            raise ValueError(
                "password must contain 1 lower case letter, "
                "1 upper case letter, 1 numeric character and 1 special character"
            )

        return value

    @validator("phone")
    @classmethod
    def validate_phone(cls, value):
        phone_pattern = r"^08\d+$"
        invalid_phone_pattern = [r"^080\d+$", r"^084\d+$", r"^086\d+$"]

        if not 10 <= len(value) <= 13:
            raise ValueError("Phone number length must between 10 - 13 digits.")

        if not re.match(phone_pattern, value):
            raise ValueError(
                "Phone number must contain only numeric character and start with 08."
            )

        # matching with phone pattern
        invalid_pattern1 = re.match(invalid_phone_pattern[0], value)
        invalid_pattern2 = re.match(invalid_phone_pattern[1], value)
        invalid_pattern3 = re.match(invalid_phone_pattern[2], value)
        if invalid_pattern1 or invalid_pattern2 or invalid_pattern3:
            raise ValueError("Please, use valid number for Indonesia provider")

        return value
