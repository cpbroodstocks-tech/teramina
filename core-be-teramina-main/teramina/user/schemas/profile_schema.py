# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class UpdateProfileSchema(Schema):
    name: str
    phone: str
    address: str
