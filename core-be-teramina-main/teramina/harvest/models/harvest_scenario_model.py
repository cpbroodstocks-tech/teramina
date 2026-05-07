# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class HarvestScenario(Document):
    cycle_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    name = fields.StringField(default="")
    params = fields.DictField()       # input params used to generate scenarios
    results = fields.ListField(fields.DictField())  # one result dict per scenario point
    saved = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cycle_id", "user_id"],
        "collection": "harvest_scenarios",
    }

    objects = QuerySetManager()
