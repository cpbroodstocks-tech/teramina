# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class AgentConversation(Document):
    """Stores per-session conversation history for the farm assistant."""
    user_id = fields.StringField(required=True)
    session_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    page_context = fields.DictField()
    messages = fields.ListField(fields.DictField())
    created_at = fields.DateTimeField(default=datetime.now)
    last_active = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", {"fields": ["user_id", "session_id"], "unique": True}],
        "collection": "agent_conversations",
    }
    objects = QuerySetManager()


class WorkflowTask(Document):
    """Farmer-facing reminders and follow-up tasks created by the agent."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    task_type = fields.StringField(
        choices=["reminder", "follow_up", "check", "action"],
        default="reminder",
    )
    title = fields.StringField(required=True)
    description = fields.StringField(default="")
    due_at = fields.DateTimeField()
    is_completed = fields.BooleanField(default=False)
    completed_at = fields.DateTimeField(null=True)
    source_alert_id = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "farm_id", "-due_at"],
        "collection": "workflow_tasks",
    }
    objects = QuerySetManager()


class AgentMemory(Document):
    """Durable memory: facts, preferences, events, advice history, and notes per farm."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    memory_type = fields.StringField(
        choices=["fact", "preference", "event", "advice", "note"],
        default="note",
    )
    content = fields.StringField(required=True)
    tags = fields.ListField(fields.StringField())
    source = fields.StringField(
        choices=["user_input", "agent_inference", "system_observation"],
        default="agent_inference",
    )
    confidence = fields.FloatField(default=0.7)
    is_verified = fields.BooleanField(default=False)
    embedding = fields.ListField(fields.FloatField())
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    expires_at = fields.DateTimeField(null=True)

    meta = {
        "indexes": [
            "user_id",
            "farm_id",
            "pond_id",
            "-created_at",
            {"fields": ["expires_at"], "expireAfterSeconds": 0, "sparse": True},
        ],
        "collection": "agent_memories",
    }
    objects = QuerySetManager()


class MemoryEntity(Document):
    """Graph node for durable farm memory."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    entity_type = fields.StringField(
        choices=["farmer", "farm", "pond", "cycle", "event", "action", "recommendation", "issue", "preference", "note"],
        required=True,
    )
    canonical_name = fields.StringField(required=True)
    metadata = fields.DictField()
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "farm_id", "entity_type", "canonical_name"],
        "collection": "memory_entities",
    }
    objects = QuerySetManager()


class MemoryRelation(Document):
    """Graph edge connecting memory entities."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    source_entity_id = fields.StringField(required=True)
    relation_type = fields.StringField(
        choices=["owns", "manages", "contains", "belongs_to", "observed", "caused_by", "treated_with", "resulted_in", "similar_to", "prefers", "mentions"],
        required=True,
    )
    target_entity_id = fields.StringField(required=True)
    confidence = fields.FloatField(default=0.7)
    source_type = fields.StringField(
        choices=["system", "farmer", "ai_inference", "imported_data"],
        default="ai_inference",
    )
    source_ref = fields.StringField(default="")
    valid_from = fields.DateTimeField(default=datetime.now)
    valid_until = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "farm_id", "source_entity_id", "target_entity_id", "relation_type"],
        "collection": "memory_relations",
    }
    objects = QuerySetManager()


class MemoryObservation(Document):
    """Graph-attached memory text with source, confidence, and lifecycle metadata."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    entity_id = fields.StringField(required=True)
    observation_type = fields.StringField(
        choices=["fact", "preference", "event_summary", "action_summary", "outcome", "risk_pattern", "note"],
        default="note",
    )
    content = fields.StringField(required=True)
    structured_data = fields.DictField()
    confidence = fields.FloatField(default=0.7)
    importance = fields.IntField(default=3, min_value=1, max_value=5)
    source_type = fields.StringField(
        choices=["system", "farmer", "ai_inference", "imported_data"],
        default="ai_inference",
    )
    source_ref = fields.StringField(default="")
    is_verified = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.now)
    expires_at = fields.DateTimeField(null=True)

    meta = {
        "indexes": [
            "user_id",
            "farm_id",
            "pond_id",
            "cycle_id",
            "-created_at",
            {"fields": ["expires_at"], "expireAfterSeconds": 0, "sparse": True},
        ],
        "collection": "memory_observations",
    }
    objects = QuerySetManager()


class MemoryEmbedding(Document):
    """Vector index entry for flat memories and graph observations."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    source_ref = fields.StringField(required=True, unique=True)
    source_kind = fields.StringField(choices=["agent_memory", "memory_observation"], required=True)
    content = fields.StringField(required=True)
    embedding = fields.ListField(fields.FloatField())
    embedding_model = fields.StringField(default="")
    content_hash = fields.StringField(default="")
    confidence = fields.FloatField(default=0.7)
    is_verified = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "farm_id", "pond_id", "source_kind", "-updated_at"],
        "collection": "memory_embeddings",
    }
    objects = QuerySetManager()


class FarmAlert(Document):
    """Proactive alerts generated by the monitoring system."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(required=True)
    cycle_id = fields.StringField(required=True)
    alert_type = fields.StringField()
    severity = fields.StringField()
    message = fields.StringField()
    data = fields.DictField()
    is_read = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.now)
    expires_at = fields.DateTimeField()
    resolved_at = fields.DateTimeField(null=True)
    resolution_note = fields.StringField(default="")
    follow_up_task_id = fields.StringField(default="")
    follow_up_scheduled_at = fields.DateTimeField(null=True)
    follow_up_completed = fields.BooleanField(default=False)
    outcome_memory_id = fields.StringField(default="")

    meta = {
        "indexes": ["user_id", "is_read", "-created_at", {"fields": ["expires_at"], "expireAfterSeconds": 0}],
        "collection": "farm_alerts",
    }
    objects = QuerySetManager()
