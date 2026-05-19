# pylint: disable=missing-class-docstring
# Django ORM models backed by Postgres + pgvector.
# These replace the MongoEngine counterparts in agent_model.py for the beachhead tables.

from django.db import models
from django.contrib.postgres.fields import ArrayField

try:
    from pgvector.django import VectorField
except ModuleNotFoundError:
    class VectorField(models.JSONField):
        def __init__(self, *args, dimensions=None, **kwargs):
            super().__init__(*args, **kwargs)


class AgentConversation(models.Model):
    user_id = models.CharField(max_length=255)
    session_id = models.CharField(max_length=255, unique=True)
    farm_id = models.CharField(max_length=255, default="")
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    page_context = models.JSONField(default=dict, blank=True)
    messages = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(fields=["user_id"], name="agent_conv_user_idx"),
            models.Index(fields=["session_id"], name="agent_conv_session_idx"),
        ]


class WorkflowTask(models.Model):
    TASK_TYPE_CHOICES = [
        ("reminder", "Reminder"),
        ("follow_up", "Follow Up"),
        ("check", "Check"),
        ("action", "Action"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255, default="")
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default="reminder")
    title = models.CharField(max_length=500)
    description = models.TextField(default="")
    due_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    source_alert_id = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(fields=["user_id", "farm_id"], name="agent_task_user_farm_idx"),
        ]


class AgentMemory(models.Model):
    MEMORY_TYPE_CHOICES = [
        ("fact", "Fact"),
        ("preference", "Preference"),
        ("event", "Event"),
        ("advice", "Advice"),
        ("note", "Note"),
    ]
    SOURCE_CHOICES = [
        ("user_input", "User Input"),
        ("agent_inference", "Agent Inference"),
        ("system_observation", "System Observation"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255, default="")
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPE_CHOICES, default="note")
    content = models.TextField()
    tags = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default="agent_inference")
    confidence = models.FloatField(default=0.7)
    is_verified = models.BooleanField(default=False)
    embedding = VectorField(dimensions=3072, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(fields=["user_id", "farm_id", "pond_id", "created_at"], name="agent_mem_farm_pond_idx"),
        ]


class MemoryEntity(models.Model):
    ENTITY_TYPE_CHOICES = [
        ("farmer", "Farmer"),
        ("farm", "Farm"),
        ("pond", "Pond"),
        ("cycle", "Cycle"),
        ("event", "Event"),
        ("action", "Action"),
        ("recommendation", "Recommendation"),
        ("issue", "Issue"),
        ("preference", "Preference"),
        ("note", "Note"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255, default="")
    entity_type = models.CharField(max_length=30, choices=ENTITY_TYPE_CHOICES)
    canonical_name = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(
                fields=["user_id", "farm_id", "entity_type", "canonical_name"],
                name="agent_entity_lookup_idx",
            ),
        ]


class MemoryRelation(models.Model):
    RELATION_TYPE_CHOICES = [
        ("owns", "Owns"),
        ("manages", "Manages"),
        ("contains", "Contains"),
        ("belongs_to", "Belongs To"),
        ("observed", "Observed"),
        ("caused_by", "Caused By"),
        ("treated_with", "Treated With"),
        ("resulted_in", "Resulted In"),
        ("similar_to", "Similar To"),
        ("prefers", "Prefers"),
        ("mentions", "Mentions"),
    ]
    SOURCE_TYPE_CHOICES = [
        ("system", "System"),
        ("farmer", "Farmer"),
        ("ai_inference", "AI Inference"),
        ("imported_data", "Imported Data"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255, default="")
    source_entity_id = models.CharField(max_length=255)
    relation_type = models.CharField(max_length=30, choices=RELATION_TYPE_CHOICES)
    target_entity_id = models.CharField(max_length=255)
    confidence = models.FloatField(default=0.7)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default="ai_inference")
    source_ref = models.CharField(max_length=500, default="")
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(
                fields=["user_id", "farm_id", "source_entity_id", "target_entity_id"],
                name="agent_relation_lookup_idx",
            ),
        ]


class MemoryObservation(models.Model):
    OBSERVATION_TYPE_CHOICES = [
        ("fact", "Fact"),
        ("preference", "Preference"),
        ("event_summary", "Event Summary"),
        ("action_summary", "Action Summary"),
        ("outcome", "Outcome"),
        ("risk_pattern", "Risk Pattern"),
        ("note", "Note"),
    ]
    SOURCE_TYPE_CHOICES = [
        ("system", "System"),
        ("farmer", "Farmer"),
        ("ai_inference", "AI Inference"),
        ("imported_data", "Imported Data"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255, default="")
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    entity_id = models.CharField(max_length=255)
    observation_type = models.CharField(max_length=20, choices=OBSERVATION_TYPE_CHOICES, default="note")
    content = models.TextField()
    structured_data = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(default=0.7)
    importance = models.IntegerField(default=3)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default="ai_inference")
    source_ref = models.CharField(max_length=500, default="")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(
                fields=["user_id", "farm_id", "pond_id", "cycle_id", "created_at"],
                name="agent_obs_farm_pond_idx",
            ),
        ]


class FarmAlert(models.Model):
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    user_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255)
    cycle_id = models.CharField(max_length=255, default="")
    alert_type = models.CharField(max_length=100, default="")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="info")
    message = models.TextField(default="")
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(default="")
    follow_up_task_id = models.CharField(max_length=255, default="")
    follow_up_scheduled_at = models.DateTimeField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    outcome_memory_id = models.CharField(max_length=255, default="")

    class Meta:
        app_label = "agent"
        indexes = [
            models.Index(fields=["user_id", "is_read", "created_at"], name="agent_alert_user_read_idx"),
            models.Index(fields=["user_id", "farm_id"], name="agent_alert_user_farm_idx"),
        ]
