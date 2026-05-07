# pylint: disable=broad-except

import logging
from celery import shared_task
from ..services.benchmark_service import BenchmarkService

logger = logging.getLogger("teramina")


@shared_task(name="benchmark.recompute_cohorts")
def recompute_cohorts():
    """Nightly Celery Beat task: recompute all benchmark cohort statistics."""
    try:
        result = BenchmarkService.recompute_cohorts()
        logger.info("Benchmark recompute complete: %s", result)
        return result
    except Exception as exc:
        logger.exception("Benchmark recompute failed: %s", exc)
        return {"error": str(exc)}
