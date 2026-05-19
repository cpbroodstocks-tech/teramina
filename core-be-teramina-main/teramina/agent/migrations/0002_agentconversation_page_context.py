from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentconversation",
            name="page_context",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
