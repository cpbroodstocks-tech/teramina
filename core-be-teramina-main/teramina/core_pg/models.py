# pylint: disable=missing-class-docstring
# Domain Postgres models — canonical Postgres schema per SECOND_BRAIN Phase 2.
# MongoDB stays as the read-only legacy source during migration.
# mongo_id links each row to its originating MongoDB document.

from django.db import models


class Farm(models.Model):
    mongo_id = models.CharField(max_length=255, unique=True, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500)
    location = models.CharField(max_length=500, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core_pg"


class Pond(models.Model):
    mongo_id = models.CharField(max_length=255, unique=True, db_index=True)
    farm_id = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500)
    size = models.FloatField(null=True, blank=True)
    depth = models.FloatField(default=1.5)
    pond_construction = models.CharField(max_length=100, default="")
    pond_shape = models.CharField(max_length=100, default="")
    is_active = models.BooleanField(default=True)
    active_cycle_id = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["farm_id", "is_active"], name="core_pg_pond_farm_active_idx"),
        ]


class Cycle(models.Model):
    mongo_id = models.CharField(max_length=255, unique=True, db_index=True)
    pond_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500, default="")
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["pond_id", "is_active"], name="core_pg_cycle_pond_active_idx"),
            models.Index(fields=["farm_id", "is_active"], name="core_pg_cycle_farm_active_idx"),
        ]


class CycleObservation(models.Model):
    """Structured daily roll-up per pond/cycle. Source of truth for AI queries."""
    cycle_id = models.CharField(max_length=255, db_index=True)
    pond_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    doc = models.IntegerField()
    recorded_at = models.DateTimeField()
    do_avg = models.FloatField(null=True, blank=True)
    temp_avg = models.FloatField(null=True, blank=True)
    nh3 = models.FloatField(null=True, blank=True)
    salinity = models.FloatField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    turbidity = models.FloatField(null=True, blank=True)
    abw = models.FloatField(null=True, blank=True)
    biomass = models.FloatField(null=True, blank=True)
    survival_rate = models.FloatField(null=True, blank=True)
    sgr = models.FloatField(null=True, blank=True)
    fcr = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=50, default="manual")
    formula_version = models.CharField(max_length=50, default="")
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        unique_together = [("cycle_id", "doc")]
        indexes = [
            models.Index(fields=["cycle_id", "doc"], name="core_pg_obs_cycle_doc_idx"),
            models.Index(fields=["pond_id", "recorded_at"], name="core_pg_obs_pond_date_idx"),
        ]


class WaterQualityReading(models.Model):
    """Raw per-parameter readings. recorded_at is the TimescaleDB hypertable time dimension."""
    PARAMETER_CHOICES = [
        ("do", "DO"),
        ("temp", "Temperature"),
        ("nh3", "NH3"),
        ("salinity", "Salinity"),
        ("ph", "pH"),
        ("turbidity", "Turbidity"),
        ("co2", "CO2"),
        ("alkalinity", "Alkalinity"),
    ]
    cycle_id = models.CharField(max_length=255, db_index=True)
    pond_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    doc = models.IntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(db_index=True)
    parameter = models.CharField(max_length=30, choices=PARAMETER_CHOICES)
    value = models.FloatField()
    unit = models.CharField(max_length=20, default="")
    source = models.CharField(max_length=30, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["cycle_id", "parameter", "recorded_at"], name="core_pg_wq_cycle_param_idx"),
            models.Index(fields=["pond_id", "recorded_at"], name="core_pg_wq_pond_date_idx"),
        ]


class FeedEvent(models.Model):
    cycle_id = models.CharField(max_length=255, db_index=True)
    pond_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    doc = models.IntegerField()
    ration_number = models.IntegerField(default=1)
    feed_ration = models.FloatField(null=True, blank=True)
    feed_given = models.FloatField(null=True, blank=True)
    feed_leftover = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["cycle_id", "doc"], name="core_pg_feed_cycle_doc_idx"),
        ]


class HarvestEvent(models.Model):
    HARVEST_TYPE_CHOICES = [
        ("partial", "Partial"),
        ("full", "Full"),
        ("emergency", "Emergency"),
    ]
    cycle_id = models.CharField(max_length=255, db_index=True)
    pond_id = models.CharField(max_length=255)
    farm_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    harvest_type = models.CharField(max_length=20, choices=HARVEST_TYPE_CHOICES, default="partial")
    harvest_date = models.DateTimeField()
    doc = models.IntegerField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    size_count = models.IntegerField(null=True, blank=True)
    price_per_kg_idr = models.FloatField(null=True, blank=True)
    revenue_idr = models.FloatField(null=True, blank=True)
    notes = models.TextField(default="")
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["cycle_id", "harvest_date"], name="core_pg_harvest_cycle_date_idx"),
        ]


class CostEvent(models.Model):
    CATEGORY_CHOICES = [
        ("feed", "Feed"),
        ("seed", "Seed/PL"),
        ("labor", "Labor"),
        ("chemical", "Chemical/Treatment"),
        ("energy", "Energy/Fuel"),
        ("equipment", "Equipment"),
        ("operational", "Operational"),
        ("other", "Other"),
    ]
    cycle_id = models.CharField(max_length=255, default="", db_index=True)
    farm_id = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="other")
    amount_idr = models.FloatField()
    event_date = models.DateField(null=True, blank=True)
    description = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["farm_id", "cycle_id"], name="core_pg_cost_farm_cycle_idx"),
        ]


class FarmerNote(models.Model):
    NOTE_TYPE_CHOICES = [
        ("text", "Text"),
        ("voice_transcript", "Voice Transcript"),
        ("photo_caption", "Photo Caption"),
    ]
    user_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255)
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    content = models.TextField()
    note_type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES, default="text")
    source_url = models.CharField(max_length=1000, default="")
    doc = models.IntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["user_id", "farm_id", "pond_id"], name="core_pg_note_farm_pond_idx"),
        ]


class Recommendation(models.Model):
    REC_TYPE_CHOICES = [
        ("feeding", "Feeding"),
        ("harvest", "Harvest"),
        ("water_quality", "Water Quality"),
        ("cost", "Cost"),
        ("health", "Health/Treatment"),
        ("general", "General"),
    ]
    user_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255)
    pond_id = models.CharField(max_length=255, default="")
    cycle_id = models.CharField(max_length=255, default="")
    recommendation_type = models.CharField(max_length=30, choices=REC_TYPE_CHOICES, default="general")
    content = models.TextField()
    reasoning = models.TextField(default="")
    source_refs = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.7)
    agent_session_id = models.CharField(max_length=255, default="")
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    outcome_note = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["user_id", "farm_id", "created_at"], name="core_pg_rec_farm_date_idx"),
        ]


class AuditEvent(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]
    user_id = models.CharField(max_length=255, db_index=True)
    farm_id = models.CharField(max_length=255, default="")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=255)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core_pg"
        indexes = [
            models.Index(fields=["user_id", "created_at"], name="core_pg_audit_user_date_idx"),
            models.Index(fields=["entity_type", "entity_id"], name="core_pg_audit_entity_idx"),
        ]
