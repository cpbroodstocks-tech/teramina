from datetime import datetime

from mongoengine import Document, fields, QuerySetManager


class ContentItem(Document):
    title = fields.StringField(required=True)
    slug = fields.StringField(required=True, unique=True)
    summary = fields.StringField(default="")
    category = fields.StringField(required=True)
    tags = fields.ListField(fields.StringField())
    language = fields.StringField(choices=["en", "id"], default="en")
    variant_group_id = fields.StringField(default="")
    variant_type = fields.StringField(choices=["master", "practical"], default="master")
    source_content_id = fields.StringField(default="")
    content_type = fields.StringField(
        choices=["article", "guide", "sop", "checklist", "template", "calculator", "report_template"],
        default="guide",
    )
    access_level = fields.StringField(choices=["free", "paid", "client", "admin"], default="free")
    body_markdown = fields.StringField(default="")
    file_url = fields.StringField(default="")
    version = fields.StringField(default="1.0")
    status = fields.StringField(
        choices=["draft", "in_review", "changes_requested", "approved", "published", "archived"],
        default="draft",
    )
    review_notes = fields.StringField(default="")
    reviewed_by = fields.StringField(default="")
    submitted_at = fields.DateTimeField(null=True)
    reviewed_at = fields.DateTimeField(null=True)
    published_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["slug", "category", "tags", "language", "variant_group_id", "variant_type", "access_level", "status", "-published_at"],
        "collection": "content_items",
    }
    objects = QuerySetManager()

    def to_dict(self, include_body=False, access_status="locked", include_workflow=False):
        data = {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "summary": self.summary,
            "category": self.category,
            "tags": list(self.tags or []),
            "language": self.language,
            "variant_group_id": self.variant_group_id,
            "variant_type": self.variant_type,
            "source_content_id": self.source_content_id,
            "content_type": self.content_type,
            "access_level": self.access_level,
            "version": self.version,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "access_status": access_status,
        }
        if include_workflow:
            data["review_notes"] = self.review_notes
            data["reviewed_by"] = self.reviewed_by
            data["submitted_at"] = self.submitted_at.isoformat() if self.submitted_at else None
            data["reviewed_at"] = self.reviewed_at.isoformat() if self.reviewed_at else None
        if include_body:
            data["body_markdown"] = self.body_markdown
            data["file_url"] = self.file_url
        return data


class ContentRevision(Document):
    content_id = fields.StringField(required=True)
    revision_number = fields.IntField(required=True, min_value=1)
    title = fields.StringField(required=True)
    summary = fields.StringField(default="")
    category = fields.StringField(required=True)
    tags = fields.ListField(fields.StringField())
    language = fields.StringField(default="en")
    variant_group_id = fields.StringField(default="")
    variant_type = fields.StringField(default="master")
    source_content_id = fields.StringField(default="")
    content_type = fields.StringField(default="guide")
    access_level = fields.StringField(default="free")
    body_markdown = fields.StringField(default="")
    file_url = fields.StringField(default="")
    version = fields.StringField(default="1.0")
    status = fields.StringField(default="draft")
    review_notes = fields.StringField(default="")
    reviewed_by = fields.StringField(default="")
    changed_by = fields.StringField(default="")
    change_note = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["content_id", "-revision_number", "-created_at"],
        "collection": "content_revisions",
    }
    objects = QuerySetManager()

    def to_dict(self, include_body=False):
        data = {
            "id": str(self.id),
            "content_id": self.content_id,
            "revision_number": self.revision_number,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "tags": list(self.tags or []),
            "language": self.language,
            "variant_group_id": self.variant_group_id,
            "variant_type": self.variant_type,
            "source_content_id": self.source_content_id,
            "content_type": self.content_type,
            "access_level": self.access_level,
            "file_url": self.file_url,
            "version": self.version,
            "status": self.status,
            "review_notes": self.review_notes,
            "reviewed_by": self.reviewed_by,
            "changed_by": self.changed_by,
            "change_note": self.change_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_body:
            data["body_markdown"] = self.body_markdown
        return data


class ContentAccess(Document):
    user_id = fields.StringField(required=True)
    content_id = fields.StringField(required=True)
    access_source = fields.StringField(
        choices=["manual", "consulting_case", "admin_grant", "invoice_paid"],
        default="manual",
    )
    expires_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "content_id", "expires_at"],
        "collection": "content_access",
    }
    objects = QuerySetManager()

    def is_valid(self):
        return not self.expires_at or self.expires_at > datetime.now()

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "content_id": self.content_id,
            "access_source": self.access_source,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid(),
        }
