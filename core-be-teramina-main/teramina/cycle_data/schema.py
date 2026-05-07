# pylint: disable=missing-class-docstring, too-few-public-methods
from ninja import Schema


class FilterWaterQuality(Schema):
    farm: str
    pond: str
    cycles: str
    start_date: str
    end_date: str
    variables: str
