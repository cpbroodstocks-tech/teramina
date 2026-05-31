from datetime import datetime

from mongoengine.errors import NotUniqueError, ValidationError

from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.content_model import ContentAccess, ContentItem, ContentRevision


def _is_admin(user) -> bool:
    return getattr(user, "role_user", "") == "admin"


WORKFLOW_STATUSES = {"draft", "in_review", "changes_requested", "approved", "published", "archived"}


class ContentService:
    @staticmethod
    def _snapshot_revision(item: ContentItem, changed_by="", change_note=""):
        latest = ContentRevision.objects(content_id=str(item.id)).order_by("-revision_number").first()
        revision = ContentRevision(
            content_id=str(item.id),
            revision_number=(latest.revision_number + 1) if latest else 1,
            title=item.title,
            summary=item.summary,
            category=item.category,
            tags=list(item.tags or []),
            language=item.language,
            variant_group_id=item.variant_group_id,
            variant_type=item.variant_type,
            source_content_id=item.source_content_id,
            content_type=item.content_type,
            access_level=item.access_level,
            body_markdown=item.body_markdown,
            file_url=item.file_url,
            version=item.version,
            status=item.status,
            review_notes=item.review_notes,
            reviewed_by=item.reviewed_by,
            changed_by=changed_by,
            change_note=change_note,
        )
        revision.save()
        return revision

    @staticmethod
    def _valid_access(user_id: str, item: ContentItem):
        if not user_id:
            return None
        access = ContentAccess.objects(user_id=user_id, content_id=str(item.id)).order_by("-created_at").first()
        if access and access.is_valid():
            return access
        return None

    @classmethod
    def access_status(cls, item: ContentItem, user_id: str = ""):
        if item.access_level == "free":
            return "free"
        access = cls._valid_access(user_id, item)
        if access:
            return "granted"
        expired = ContentAccess.objects(user_id=user_id, content_id=str(item.id), expires_at__lte=datetime.now()).first() if user_id else None
        return "expired" if expired else "locked"

    @classmethod
    def list_items(cls, user_id="", category="", tag="", content_type="", language="", access_level="", variant_group_id="", variant_type=""):
        query = {"status": "published"}
        if category:
            query["category"] = category
        if tag:
            query["tags"] = tag
        if content_type:
            query["content_type"] = content_type
        if language:
            query["language"] = language
        if variant_group_id:
            query["variant_group_id"] = variant_group_id
        if variant_type:
            query["variant_type"] = variant_type
        if access_level:
            query["access_level"] = access_level

        items = []
        for item in ContentItem.objects(**query).order_by("-published_at", "title"):
            status = cls.access_status(item, user_id)
            items.append(item.to_dict(include_body=item.access_level == "free" or status == "granted", access_status=status))

        return 200, DataSuccessSchema(code=200, message="OK", payload={"items": items})

    @classmethod
    def admin_list_items(cls, user, status="", access_level="", language="", variant_group_id="", variant_type=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status
        if access_level:
            query["access_level"] = access_level
        if language:
            query["language"] = language
        if variant_group_id:
            query["variant_group_id"] = variant_group_id
        if variant_type:
            query["variant_type"] = variant_type

        items = [
            item.to_dict(include_body=False, access_status="granted", include_workflow=True)
            for item in ContentItem.objects(**query).order_by("-updated_at", "title")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"items": items})

    @staticmethod
    def admin_list_access(user, user_id="", content_id=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if user_id:
            query["user_id"] = user_id
        if content_id:
            query["content_id"] = content_id

        access = [item.to_dict() for item in ContentAccess.objects(**query).order_by("-created_at")]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"access": access})

    @staticmethod
    def admin_get_item(user, content_id):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        item = ContentItem.objects(id=content_id).first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={"item": item.to_dict(include_body=True, access_status="granted", include_workflow=True)},
        )

    @staticmethod
    def admin_list_revisions(user, content_id):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        item = ContentItem.objects(id=content_id).first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")
        revisions = [
            revision.to_dict(include_body=False)
            for revision in ContentRevision.objects(content_id=content_id).order_by("-revision_number")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"revisions": revisions})

    @classmethod
    def get_item(cls, slug: str, user_id=""):
        item = ContentItem.objects(slug=slug, status="published").first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")

        status = cls.access_status(item, user_id)
        include_body = item.access_level == "free" or status == "granted"
        return 200, DataSuccessSchema(code=200, message="OK", payload={"item": item.to_dict(include_body=include_body, access_status=status)})

    @classmethod
    def get_downloadable_item(cls, slug: str, user_id=""):
        item = ContentItem.objects(slug=slug, status="published").first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")

        status = cls.access_status(item, user_id)
        if item.access_level != "free" and status != "granted":
            return 401, DataErrorSchema(code=401, message="Content access required")
        return 200, item

    @staticmethod
    def create_item(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        try:
            payload = data.dict()
            change_note = payload.pop("change_note", "Initial version")
            if payload.get("status") == "published" and not payload.get("published_at"):
                payload["published_at"] = datetime.now()
            item = ContentItem(**payload)
            item.save()
            ContentService._snapshot_revision(item, changed_by=str(user.id), change_note=change_note)
            return 200, DataSuccessSchema(
                code=200,
                message="Content created",
                payload={"item": item.to_dict(include_body=True, access_status="granted", include_workflow=True)},
            )
        except (NotUniqueError, ValidationError) as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def update_item(user, content_id, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        item = ContentItem.objects(id=content_id).first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")

        updates = data.dict(exclude_unset=True)
        change_note = updates.pop("change_note", "Content updated")
        for key, value in updates.items():
            setattr(item, key, value)
        if updates.get("status") == "published" and not item.published_at:
            item.published_at = datetime.now()
        item.updated_at = datetime.now()
        item.save()
        ContentService._snapshot_revision(item, changed_by=str(user.id), change_note=change_note)
        return 200, DataSuccessSchema(
            code=200,
            message="Content updated",
            payload={"item": item.to_dict(include_body=True, access_status="granted", include_workflow=True)},
        )

    @staticmethod
    def transition_workflow(user, content_id, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        if data.status not in WORKFLOW_STATUSES:
            return 400, DataErrorSchema(code=400, message="Invalid content workflow status")

        item = ContentItem.objects(id=content_id).first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")

        previous_status = item.status
        now = datetime.now()
        item.status = data.status
        if data.status == "in_review" and not item.submitted_at:
            item.submitted_at = now
        if data.status in {"changes_requested", "approved", "published"}:
            item.reviewed_by = str(user.id)
            item.reviewed_at = now
            item.review_notes = data.review_note
        if data.status == "published":
            item.published_at = item.published_at or now
        elif previous_status == "published":
            item.published_at = None
        item.updated_at = now
        item.save()

        note = data.review_note or f"Workflow transition: {previous_status} -> {data.status}"
        ContentService._snapshot_revision(item, changed_by=str(user.id), change_note=note)
        return 200, DataSuccessSchema(
            code=200,
            message="Content workflow updated",
            payload={"item": item.to_dict(include_body=True, access_status="granted", include_workflow=True)},
        )

    @staticmethod
    def grant_access(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")
        item = ContentItem.objects(id=data.content_id).first()
        if not item:
            return 404, DataErrorSchema(code=404, message="Content not found")
        access = ContentAccess(
            user_id=data.user_id,
            content_id=data.content_id,
            access_source=data.access_source,
            expires_at=data.expires_at,
        )
        access.save()
        return 200, DataSuccessSchema(
            code=200,
            message="Access granted",
            payload={"access": access.to_dict()},
        )
