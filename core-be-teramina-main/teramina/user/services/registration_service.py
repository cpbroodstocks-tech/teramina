# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja.errors import ValidationError
from django.contrib.auth.hashers import make_password
from mongoengine.errors import DoesNotExist, InvalidQueryError, FieldDoesNotExist

from ..schemas.registration_schema import RegisterSchema
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema

from ..models.user_model import User


class RegistrationService:
    def register(self, data: RegisterSchema):
        """register function"""
        self.__validate_register_request_body(data.email, data.phone)

        try:
            user = User(
                name=data.name,
                email=data.email,
                phone=data.phone,
                password=make_password(data.password),
            )
            user.save()
        except InvalidQueryError:
            return 400, DataErrorSchema(code=400, message="Failed to add data")

        except FieldDoesNotExist:
            return 400, DataErrorSchema(code=400, message="Failed to add data")

        return 200, DataSuccessSchema(
            code=200, message="User successfully registered.", payload={}
        )

    def __validate_register_request_body(self, email, phone):
        is_email_duplicate = self.__validate_duplicate_email(email)
        is_phone_duplicate = self.__validate_duplicate_phone(phone)

        if is_email_duplicate | is_phone_duplicate:
            duplicate_errors = []
            error_data = {
                "loc": ["body", "data", "email"],
                "msg": "Email already exists.",
                "type": "value_error",
            }

            if is_email_duplicate:
                duplicate_errors.append(error_data)

            if is_phone_duplicate:
                error_data["msg"] = "Phone number already exists."
                duplicate_errors.append(error_data)

            raise ValidationError(duplicate_errors)

    @staticmethod
    def __validate_duplicate_email(email):
        try:
            user = User.objects(email=email).first()
            if not user:
                return False

            return True
        except DoesNotExist:
            return False

    @staticmethod
    def __validate_duplicate_phone(phone):
        try:
            user = User.objects(phone=phone).first()
            if not user:
                return False

            return True
        except DoesNotExist:
            return False
