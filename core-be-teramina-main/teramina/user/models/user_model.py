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
    