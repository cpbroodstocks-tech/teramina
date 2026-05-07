# pylint: disable=missing-class-docstring,no-member

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class Pond(Document):
    name = fields.StringField()
    size = fields.FloatField()
    depth = fields.FloatField(default=1.5)
    pond_construction = fields.StringField()
    pond_shape = fields.StringField()
    farm_id = fields.StringField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now())
    last_updated = fields.DateTimeField()
    active_cycle_id = fields.StringField()

    meta = {"indexes": ["farm_id"]}

    # Define the objects manager
    objects = QuerySetManager()

    def to_dict(self):
        """convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "depth": self.depth,
            "pond_construction": self.pond_construction,
            "farm_id": self.farm_id,
            "pond_shape": self.pond_shape,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "is_active": self.is_active,
            "active_cycle_id": self.active_cycle_id
        }
