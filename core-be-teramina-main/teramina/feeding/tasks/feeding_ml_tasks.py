# pylint: disable=broad-except

import logging
from celery import shared_task

from teramina.feeding.services.feeding_ml_service import FeedingMLService

logger = logging.getLogger("teramina")


@shared_task(name="teramina.feeding.tasks.feeding_ml_tasks.retrain_feeding_model")
def retrain_feeding_model():
    """Retrain the XGBoost feeding recommendation model on top-25% FCR cycles."""
    logger.info("Starting feeding model retraining task")
    try:
        metrics = FeedingMLService.train_model()
        logger.info("Feeding model retraining complete: %s", metrics)
        return metrics
    except Exception as exc:
        logger.exception("Feeding model retraining failed: %s", exc)
        return {"error": str(exc)}
