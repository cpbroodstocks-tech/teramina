"""
Convert water_quality_readings to a TimescaleDB hypertable.
Requires TimescaleDB extension on the Postgres instance.
Safe to run on vanilla Postgres — catches the extension-not-found error and continues.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core_pg", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Only proceed if timescaledb is available
                    IF EXISTS (
                        SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'
                    ) THEN
                        CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
                        PERFORM create_hypertable(
                            'core_pg_waterqualityreading',
                            'recorded_at',
                            if_not_exists => TRUE,
                            migrate_data  => TRUE
                        );
                    END IF;
                END
                $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
                    ) THEN
                        SELECT revert_hypertable('core_pg_waterqualityreading');
                    END IF;
                END
                $$;
            """,
        ),
    ]
