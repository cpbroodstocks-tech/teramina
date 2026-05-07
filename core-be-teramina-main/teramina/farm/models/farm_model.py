# pylint: disable=missing-class-docstring, no-member

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class Farm(Document):
    name = fields.StringField()
    location = fields.StringField()
    user_id = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.now())
    last_updated = fields.DateTimeField()

    meta = {"indexes": ["user_id"]}

    # Define the objects manager
    objects = QuerySetManager()

    def to_dict(self):
        """convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "location": self.location,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
