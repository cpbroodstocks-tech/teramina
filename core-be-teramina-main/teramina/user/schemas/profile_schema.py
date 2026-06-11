# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema
from pydantic import Field


class UpdateProfileSchema(Schema):
    name: str
    phone: str
    address: str


class FcmTokenSchema(Schema):
    token: str


class DemoExperienceEventSchema(Schema):
    event_name: str
    properties: dict[str, str] = Field(default_factory=dict)


class DemoExperienceUpdateSchema(Schema):
    checklist_dismissed: bool


class DemoExperienceResetSchema(Schema):
    confirmed: bool = False
