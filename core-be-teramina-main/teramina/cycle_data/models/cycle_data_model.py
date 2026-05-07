# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class CycleData(Document):
    cycle_id = fields.StringField()
    result_data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    meta = {"indexes": ["cycle_id"]}

    # Define the objects manager
    objects = QuerySetManager()

class ResultData(Document):
    cycle_id = fields.StringField()
    result_data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    meta = {"indexes": ["cycle_id"]}

    # Define the objects manager
    objects = QuerySetManager()

class ForecastData(Document):
    cycle_id = fields.StringField()
    result_data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    meta = {"indexes": ["cycle_id"]}

    # Define the objects manager
    objects = QuerySetManager()
