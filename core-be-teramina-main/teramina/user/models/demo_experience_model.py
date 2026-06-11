from datetime import datetime

from mongoengine import Document, fields, QuerySetManager


class DemoExperienceState(Document):
    user_id = fields.StringField(required=True, unique=True)
    bundle_version = fields.StringField(default="")
    first_opened_at = fields.DateTimeField(null=True)
    checklist_dismissed = fields.BooleanField(default=False)
    completed_steps = fields.ListField(fields.StringField())
    seen_scenarios = fields.ListField(fields.StringField())
    reset_count = fields.IntField(default=0)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {"indexes": ["user_id"], "collection": "demo_experience_states"}
    objects = QuerySetManager()


class ProductEvent(Document):
    user_id = fields.StringField(required=True)
    event_name = fields.StringField(required=True)
    properties = fields.DictField()
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {"indexes": ["user_id", "event_name", "-created_at"], "collection": "product_events"}
    objects = QuerySetManager()
