# pylint: disable=missing-class-docstring, too-few-public-methods

from typing import Optional
from ninja import Schema
from pydantic import ConfigDict


class FeedDataSchema(Schema):
    ration_number: int
    feed_given: float
    feed_leftover: Optional[float] = None   # optional: farmer may skip tray reading
    date: str

    model_config = ConfigDict(json_schema_extra={
            "name": "Feed Data",
            "example": {
                "ration_number": 1,
                "feed_given": 19.5,
                "feed_leftover": 1.5,       # can be omitted
                "date": "02/08/2023",
            },
        })


class FeedUpdateSchema(Schema):
    feed_given: float
    feed_leftover: Optional[float] = None   # optional: farmer may skip tray reading

    model_config = ConfigDict(json_schema_extra={
            "name": "Feed Update Data",
            "example": {"feed_given": 19.5, "feed_leftover": 1.5},
        })
