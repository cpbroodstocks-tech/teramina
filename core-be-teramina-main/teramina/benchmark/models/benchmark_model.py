# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class BenchmarkParticipation(Document):
    """Tracks which farms have opted in to anonymous benchmarking."""
    farm_id = fields.StringField(required=True, unique=True)
    user_id = fields.StringField(required=True)
    opted_in = fields.BooleanField(default=False)
    opted_in_at = fields.DateTimeField()
    opted_out_at = fields.DateTimeField()

    meta = {
        "indexes": ["farm_id", "user_id"],
        "collection": "benchmark_participation",
    }
    objects = QuerySetManager()


class BenchmarkCohort(Document):
    """
    Aggregated anonymous statistics for a cohort of farms.
    Recomputed nightly by Celery Beat.
    Suppressed (not served) when sample_count < MIN_COHORT_SIZE.
    """
    cohort_key = fields.StringField(required=True, unique=True)  # hash of dimensions
    species = fields.StringField(default="vannamei")
    doc_bucket = fields.StringField()          # "1-60"|"61-90"|"91-120"|"121+"
    density_bucket = fields.StringField()      # "<50"|"50-100"|"100-200"|">200"
    region = fields.StringField(default="")
    pond_size_bucket = fields.StringField()    # "<500"|"500-2000"|">2000"

    sample_count = fields.IntField(default=0)  # number of farms contributing
    cycle_count = fields.IntField(default=0)   # total completed cycles

    # Each metric stored as {p10, p25, p50, p75, p90, mean}
    fcr = fields.DictField()
    sr = fields.DictField()
    adg = fields.DictField()
    biomass_yield = fields.DictField()   # ton/ha
    cost_per_kg = fields.DictField()
    revenue_per_m2 = fields.DictField()

    suppressed = fields.BooleanField(default=False)
    computed_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cohort_key"],
        "collection": "benchmark_cohorts",
    }
    objects = QuerySetManager()


class CompletedCycleMetrics(Document):
    """
    Stores final metrics for a completed cycle, used in cohort aggregation.
    Populated when a cycle is closed (is_active set to False).
    Only for opted-in farms.
    """
    cycle_id = fields.StringField(required=True, unique=True)
    farm_id = fields.StringField(required=True)
    pond_id = fields.StringField()
    user_id = fields.StringField()

    # Cohort dimensions
    region = fields.StringField(default="")
    stocking_density = fields.FloatField()    # ekor/m²
    pond_size_m2 = fields.FloatField()
    final_doc = fields.IntField()

    # Outcome metrics
    fcr_final = fields.FloatField()
    sr_final_pct = fields.FloatField()
    adg_avg = fields.FloatField()            # g/day
    biomass_yield_ton_per_ha = fields.FloatField()
    cost_per_kg_idr = fields.FloatField()
    revenue_per_m2_idr = fields.FloatField()

    computed_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["farm_id", "cycle_id"],
        "collection": "completed_cycle_metrics",
    }
    objects = QuerySetManager()
