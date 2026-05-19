import django.contrib.postgres.fields
import django.db.models.deletion
import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        pgvector.django.VectorExtension(),
        migrations.CreateModel(
            name="AgentConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("session_id", models.CharField(max_length=255, unique=True)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("pond_id", models.CharField(default="", max_length=255)),
                ("cycle_id", models.CharField(default="", max_length=255)),
                ("messages", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_active", models.DateTimeField(auto_now=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="agentconversation",
            index=models.Index(fields=["user_id"], name="agent_conv_user_idx"),
        ),
        migrations.AddIndex(
            model_name="agentconversation",
            index=models.Index(fields=["session_id"], name="agent_conv_session_idx"),
        ),
        migrations.CreateModel(
            name="WorkflowTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("pond_id", models.CharField(default="", max_length=255)),
                ("cycle_id", models.CharField(default="", max_length=255)),
                ("task_type", models.CharField(
                    choices=[("reminder", "Reminder"), ("follow_up", "Follow Up"), ("check", "Check"), ("action", "Action")],
                    default="reminder", max_length=20,
                )),
                ("title", models.CharField(max_length=500)),
                ("description", models.TextField(default="")),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("is_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("source_alert_id", models.CharField(default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="workflowtask",
            index=models.Index(fields=["user_id", "farm_id"], name="agent_task_user_farm_idx"),
        ),
        migrations.CreateModel(
            name="AgentMemory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("pond_id", models.CharField(default="", max_length=255)),
                ("cycle_id", models.CharField(default="", max_length=255)),
                ("memory_type", models.CharField(
                    choices=[("fact", "Fact"), ("preference", "Preference"), ("event", "Event"), ("advice", "Advice"), ("note", "Note")],
                    default="note", max_length=20,
                )),
                ("content", models.TextField()),
                ("tags", django.contrib.postgres.fields.ArrayField(
                    base_field=models.CharField(max_length=200), blank=True, default=list, size=None,
                )),
                ("source", models.CharField(
                    choices=[("user_input", "User Input"), ("agent_inference", "Agent Inference"), ("system_observation", "System Observation")],
                    default="agent_inference", max_length=30,
                )),
                ("confidence", models.FloatField(default=0.7)),
                ("is_verified", models.BooleanField(default=False)),
                ("embedding", pgvector.django.VectorField(blank=True, dimensions=3072, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="agentmemory",
            index=models.Index(fields=["user_id", "farm_id", "pond_id", "created_at"], name="agent_mem_farm_pond_idx"),
        ),
        migrations.CreateModel(
            name="MemoryEntity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("entity_type", models.CharField(
                    choices=[
                        ("farmer", "Farmer"), ("farm", "Farm"), ("pond", "Pond"), ("cycle", "Cycle"),
                        ("event", "Event"), ("action", "Action"), ("recommendation", "Recommendation"),
                        ("issue", "Issue"), ("preference", "Preference"), ("note", "Note"),
                    ],
                    max_length=30,
                )),
                ("canonical_name", models.CharField(max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="memoryentity",
            index=models.Index(
                fields=["user_id", "farm_id", "entity_type", "canonical_name"],
                name="agent_entity_lookup_idx",
            ),
        ),
        migrations.CreateModel(
            name="MemoryRelation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("source_entity_id", models.CharField(max_length=255)),
                ("relation_type", models.CharField(
                    choices=[
                        ("owns", "Owns"), ("manages", "Manages"), ("contains", "Contains"),
                        ("belongs_to", "Belongs To"), ("observed", "Observed"), ("caused_by", "Caused By"),
                        ("treated_with", "Treated With"), ("resulted_in", "Resulted In"),
                        ("similar_to", "Similar To"), ("prefers", "Prefers"), ("mentions", "Mentions"),
                    ],
                    max_length=30,
                )),
                ("target_entity_id", models.CharField(max_length=255)),
                ("confidence", models.FloatField(default=0.7)),
                ("source_type", models.CharField(
                    choices=[("system", "System"), ("farmer", "Farmer"), ("ai_inference", "AI Inference"), ("imported_data", "Imported Data")],
                    default="ai_inference", max_length=20,
                )),
                ("source_ref", models.CharField(default="", max_length=500)),
                ("valid_from", models.DateTimeField(auto_now_add=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="memoryrelation",
            index=models.Index(
                fields=["user_id", "farm_id", "source_entity_id", "target_entity_id"],
                name="agent_relation_lookup_idx",
            ),
        ),
        migrations.CreateModel(
            name="MemoryObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(default="", max_length=255)),
                ("pond_id", models.CharField(default="", max_length=255)),
                ("cycle_id", models.CharField(default="", max_length=255)),
                ("entity_id", models.CharField(max_length=255)),
                ("observation_type", models.CharField(
                    choices=[
                        ("fact", "Fact"), ("preference", "Preference"), ("event_summary", "Event Summary"),
                        ("action_summary", "Action Summary"), ("outcome", "Outcome"),
                        ("risk_pattern", "Risk Pattern"), ("note", "Note"),
                    ],
                    default="note", max_length=20,
                )),
                ("content", models.TextField()),
                ("structured_data", models.JSONField(blank=True, default=dict)),
                ("confidence", models.FloatField(default=0.7)),
                ("importance", models.IntegerField(default=3)),
                ("source_type", models.CharField(
                    choices=[("system", "System"), ("farmer", "Farmer"), ("ai_inference", "AI Inference"), ("imported_data", "Imported Data")],
                    default="ai_inference", max_length=20,
                )),
                ("source_ref", models.CharField(default="", max_length=500)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="memoryobservation",
            index=models.Index(
                fields=["user_id", "farm_id", "pond_id", "cycle_id", "created_at"],
                name="agent_obs_farm_pond_idx",
            ),
        ),
        migrations.CreateModel(
            name="FarmAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=255)),
                ("farm_id", models.CharField(max_length=255)),
                ("cycle_id", models.CharField(default="", max_length=255)),
                ("alert_type", models.CharField(default="", max_length=100)),
                ("severity", models.CharField(
                    choices=[("info", "Info"), ("warning", "Warning"), ("critical", "Critical")],
                    default="info", max_length=20,
                )),
                ("message", models.TextField(default="")),
                ("data", models.JSONField(blank=True, default=dict)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_note", models.TextField(default="")),
                ("follow_up_task_id", models.CharField(default="", max_length=255)),
                ("follow_up_scheduled_at", models.DateTimeField(blank=True, null=True)),
                ("follow_up_completed", models.BooleanField(default=False)),
                ("outcome_memory_id", models.CharField(default="", max_length=255)),
            ],
            options={"app_label": "agent"},
        ),
        migrations.AddIndex(
            model_name="farmalert",
            index=models.Index(fields=["user_id", "is_read", "created_at"], name="agent_alert_user_read_idx"),
        ),
        migrations.AddIndex(
            model_name="farmalert",
            index=models.Index(fields=["user_id", "farm_id"], name="agent_alert_user_farm_idx"),
        ),
    ]
