from datetime import datetime

from mongoengine import Document, fields, QuerySetManager


class ServicePackage(Document):
    name = fields.StringField(required=True)
    slug = fields.StringField(required=True, unique=True)
    segment = fields.StringField(
        choices=["farm", "hatchery", "investor", "input_company", "retainer"],
        required=True,
    )
    description = fields.StringField(default="")
    deliverables = fields.ListField(fields.StringField())
    required_data = fields.ListField(fields.StringField())
    price_min_idr = fields.IntField(null=True)
    price_max_idr = fields.IntField(null=True)
    is_active = fields.BooleanField(default=True)
    sort_order = fields.IntField(default=0)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["slug", "segment", "is_active", "sort_order"],
        "collection": "service_packages",
    }
    objects = QuerySetManager()

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "segment": self.segment,
            "description": self.description,
            "deliverables": list(self.deliverables or []),
            "required_data": list(self.required_data or []),
            "price_min_idr": self.price_min_idr,
            "price_max_idr": self.price_max_idr,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
        }


class AdvisoryCase(Document):
    user_id = fields.StringField(required=True)
    service_package_id = fields.StringField(default="")
    case_type = fields.StringField(
        choices=["farm_diagnostic", "crop_planning", "hatchery_review", "procurement_advisory", "investor_due_diligence", "retainer"],
        required=True,
    )
    status = fields.StringField(
        choices=["inquiry", "awaiting_data", "in_review", "report_ready", "closed", "cancelled"],
        default="inquiry",
    )
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    title = fields.StringField(default="")
    intake_data = fields.DictField()
    uploaded_files = fields.ListField(fields.DictField())
    expert_notes = fields.StringField(default="")
    report_id = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "case_type", "status", "-created_at"],
        "collection": "advisory_cases",
    }
    objects = QuerySetManager()

    def to_dict(self, include_private=False):
        uploaded_files = []
        for file_ref in self.uploaded_files or []:
            item = {
                "file_id": file_ref.get("file_id", ""),
                "name": file_ref.get("name", ""),
                "url": file_ref.get("url", ""),
                "content_type": file_ref.get("content_type", ""),
                "description": file_ref.get("description", ""),
                "access_scope": file_ref.get("access_scope", ""),
                "uploaded_by": file_ref.get("uploaded_by", ""),
                "uploaded_at": file_ref.get("uploaded_at", ""),
            }
            if include_private:
                item["case_id"] = file_ref.get("case_id", "")
                item["user_id"] = file_ref.get("user_id", "")
            uploaded_files.append(item)
        data = {
            "id": str(self.id),
            "service_package_id": self.service_package_id,
            "case_type": self.case_type,
            "status": self.status,
            "farm_id": self.farm_id,
            "pond_id": self.pond_id,
            "cycle_id": self.cycle_id,
            "title": self.title,
            "intake_data": dict(self.intake_data or {}),
            "uploaded_files": uploaded_files,
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_private:
            data["expert_notes"] = self.expert_notes
            data["user_id"] = self.user_id
        return data


class AdvisoryReport(Document):
    case_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    title = fields.StringField(required=True)
    executive_summary = fields.StringField(default="")
    data_received = fields.ListField(fields.StringField())
    key_findings = fields.ListField(fields.StringField())
    likely_causes = fields.ListField(fields.StringField())
    technical_interpretation = fields.StringField(default="")
    economic_implication = fields.StringField(default="")
    corrective_action_plan = fields.ListField(fields.StringField())
    monitoring_plan = fields.ListField(fields.StringField())
    assumptions_and_limits = fields.ListField(fields.StringField())
    source_citations = fields.ListField(fields.DictField())
    generated_from_brief_log_id = fields.StringField(default="")
    review_note = fields.StringField(default="")
    reviewed_by = fields.StringField(default="")
    reviewed_at = fields.DateTimeField(null=True)
    file_url = fields.StringField(default="")
    status = fields.StringField(choices=["draft", "expert_review_required", "delivered"], default="draft")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    delivered_at = fields.DateTimeField(null=True)

    meta = {
        "indexes": ["case_id", "user_id", "status", "-created_at"],
        "collection": "advisory_reports",
    }
    objects = QuerySetManager()

    def to_dict(self, include_private=False):
        data = {
            "id": str(self.id),
            "case_id": self.case_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "data_received": list(self.data_received or []),
            "key_findings": list(self.key_findings or []),
            "likely_causes": list(self.likely_causes or []),
            "technical_interpretation": self.technical_interpretation,
            "economic_implication": self.economic_implication,
            "corrective_action_plan": list(self.corrective_action_plan or []),
            "monitoring_plan": list(self.monitoring_plan or []),
            "assumptions_and_limits": list(self.assumptions_and_limits or []),
            "source_citations": list(self.source_citations or []),
            "generated_from_brief_log_id": self.generated_from_brief_log_id,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "file_url": self.file_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }
        if include_private:
            data["user_id"] = self.user_id
        return data


class AdvisoryExpertReview(Document):
    case_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    reviewer_id = fields.StringField(default="")
    review_type = fields.StringField(default="technical")
    summary = fields.StringField(default="")
    findings = fields.ListField(fields.StringField())
    recommendations = fields.ListField(fields.StringField())
    risk_flags = fields.ListField(fields.StringField())
    next_actions = fields.ListField(fields.StringField())
    status = fields.StringField(choices=["draft", "delivered"], default="draft")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    delivered_at = fields.DateTimeField(null=True)

    meta = {
        "indexes": ["case_id", "user_id", "status", "-created_at"],
        "collection": "advisory_expert_reviews",
    }
    objects = QuerySetManager()

    def to_dict(self, include_private=False):
        data = {
            "id": str(self.id),
            "case_id": self.case_id,
            "review_type": self.review_type,
            "summary": self.summary,
            "findings": list(self.findings or []),
            "recommendations": list(self.recommendations or []),
            "risk_flags": list(self.risk_flags or []),
            "next_actions": list(self.next_actions or []),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }
        if include_private:
            data["user_id"] = self.user_id
            data["reviewer_id"] = self.reviewer_id
        return data


class RetainerCadence(Document):
    case_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    cadence_type = fields.StringField(choices=["weekly", "biweekly", "monthly", "custom"], default="monthly")
    status = fields.StringField(choices=["active", "paused", "completed", "cancelled"], default="active")
    last_review_at = fields.DateTimeField(null=True)
    next_review_at = fields.DateTimeField(null=True)
    agenda = fields.ListField(fields.StringField())
    notes = fields.StringField(default="")
    created_by = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["case_id", "user_id", "status", "next_review_at"],
        "collection": "retainer_cadences",
    }
    objects = QuerySetManager()

    def to_dict(self, include_private=False):
        data = {
            "id": str(self.id),
            "case_id": self.case_id,
            "cadence_type": self.cadence_type,
            "status": self.status,
            "last_review_at": self.last_review_at.isoformat() if self.last_review_at else None,
            "next_review_at": self.next_review_at.isoformat() if self.next_review_at else None,
            "agenda": list(self.agenda or []),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_private:
            data["user_id"] = self.user_id
            data["created_by"] = self.created_by
        return data


class AdvisorySourceEmbedding(Document):
    source_ref = fields.StringField(required=True, unique=True)
    source_kind = fields.StringField(choices=["content_item", "advisory_report", "expert_review"], required=True)
    source_id = fields.StringField(required=True)
    title = fields.StringField(default="")
    category = fields.StringField(default="")
    snippet = fields.StringField(default="")
    content = fields.StringField(default="")
    user_id = fields.StringField(default="")
    case_id = fields.StringField(default="")
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    access_scope = fields.StringField(choices=["global", "case_private"], default="global")
    access_level = fields.StringField(default="")
    language = fields.StringField(default="")
    url = fields.StringField(default="")
    embedding = fields.ListField(fields.FloatField())
    embedding_model = fields.StringField(default="")
    content_hash = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["source_ref", "source_kind", "user_id", "case_id", "farm_id", "pond_id", "cycle_id", "-updated_at"],
        "collection": "advisory_source_embeddings",
    }
    objects = QuerySetManager()

    def to_citation(self, score=0.0):
        return {
            "source_ref": self.source_ref,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "title": self.title,
            "category": self.category,
            "snippet": self.snippet,
            "score": round(score, 4),
            "user_id": self.user_id,
            "case_id": self.case_id,
            "farm_id": self.farm_id,
            "pond_id": self.pond_id,
            "cycle_id": self.cycle_id,
            "access_scope": self.access_scope,
            "access_level": self.access_level,
            "language": self.language,
            "url": self.url,
        }


class AdvisoryAssistantBriefLog(Document):
    case_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    generated_by = fields.StringField(default="")
    status = fields.StringField(choices=["generated", "accepted", "discarded"], default="generated")
    query = fields.StringField(default="")
    missing_data = fields.ListField(fields.StringField())
    source_citations = fields.ListField(fields.DictField())
    draft_report = fields.DictField()
    accepted_report_id = fields.StringField(default="")
    accepted_by = fields.StringField(default="")
    accepted_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["case_id", "user_id", "status", "-created_at"],
        "collection": "advisory_assistant_brief_logs",
    }
    objects = QuerySetManager()

    def to_dict(self):
        return {
            "id": str(self.id),
            "case_id": self.case_id,
            "user_id": self.user_id,
            "generated_by": self.generated_by,
            "status": self.status,
            "query": self.query,
            "missing_data": list(self.missing_data or []),
            "source_citations": list(self.source_citations or []),
            "draft_report": dict(self.draft_report or {}),
            "accepted_report_id": self.accepted_report_id,
            "accepted_by": self.accepted_by,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
