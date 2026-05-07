# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class CostData(Document):
    farm_id = fields.StringField()
    start_date = fields.StringField()
    end_date = fields.StringField()
    data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()
