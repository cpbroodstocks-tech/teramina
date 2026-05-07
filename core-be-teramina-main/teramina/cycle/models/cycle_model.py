# pylint: disable=missing-class-docstring, no-member

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class Cycle(Document):
    name = fields.StringField()
    start_date = fields.DateTimeField()
    pond_id = fields.StringField()
    last_updated = fields.DateTimeField()
    is_active = fields.BooleanField(default=True)
    vector_list = fields.ListField()

    meta = {"indexes": ["pond_id"]}

    # Define the objects manager
    objects = QuerySetManager()

    def to_dict(self):
        """convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "pond_id": self.pond_id,
            "last_updated": self.last_updated,
            "is_active": self.is_active,
            "vector_list": self.vector_list
        }


class Data(Document):
    cycle_id = fields.StringField()
    data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()
