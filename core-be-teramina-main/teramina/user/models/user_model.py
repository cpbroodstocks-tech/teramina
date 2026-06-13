# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class User(Document):
    name = fields.StringField()
    phone = fields.StringField()
    email = fields.StringField()
    picture = fields.StringField()
    address = fields.StringField()
    password = fields.StringField()
    role_user = fields.StringField()
    is_there_data = fields.BooleanField(default=False)
    fcm_token = fields.StringField(default=None)
    created_at = fields.DateTimeField(default=datetime.now())

    meta = {"indexes": [{"fields": ["email"], "unique": True}]}

    # Define the objects manager
    objects = QuerySetManager()


class BetaAccessRequest(Document):
    email = fields.EmailField(required=True, unique=True)
    name = fields.StringField(default="")
    source = fields.StringField(default="landing")
    status = fields.StringField(
        choices=["pending", "approved", "rejected"],
        default="pending",
    )
    admin_note = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["email", "status", "-created_at"],
        "collection": "beta_access_requests",
    }
    objects = QuerySetManager()

    def to_dict(self, include_private=False):
        data = {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_private:
            data["admin_note"] = self.admin_note
        return data
