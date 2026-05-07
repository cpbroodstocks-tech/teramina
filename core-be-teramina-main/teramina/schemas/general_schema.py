# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class DataErrorSchema(Schema):
    code: int
    message: str


class GetListSuccessSchema(Schema):
    code: int
    message: str
    payload: list


class DataSuccessSchema(Schema):
    code: int
    message: str
    payload: dict
