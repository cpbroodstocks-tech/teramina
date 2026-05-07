# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class HarvestRecord(Document):
    cycle_id = fields.StringField()
    harvest_data = fields.DictField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()
