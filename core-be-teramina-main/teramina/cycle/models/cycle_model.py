# pylint: disable=missing-class-docstring, no-member

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class Cycle(Document):
    name = fields.StringField()
    start_date = fields.DateTimeField()
    pond_id = fields.StringField()
    demo_scenario = fields.StringField(default="")
    last_updated = fields.DateTimeField()
    is_active = fields.BooleanField(default=True)
    archived_at = fields.DateTimeField()
    archived_by = fields.StringField(default="")
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
            "demo_scenario": self.demo_scenario,
            "last_updated": self.last_updated,
            "is_active": self.is_active,
            "archived_at": self.archived_at,
            "archived_by": self.archived_by,
            "vector_list": self.vector_list
        }


class Data(Document):
    cycle_id = fields.StringField()
    data = fields.ListField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()
