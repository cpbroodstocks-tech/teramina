# pylint: disable=broad-except

import base64
import logging

from asgiref.sync import async_to_sync
from celery import shared_task

from teramina.dashboard.services.historical.overview import DashboardOverview
from teramina.helpers.report_service import generate_pdf_report_with_data

logger = logging.getLogger("teramina")


@shared_task(name="dashboard.generate_overview_report")
def generate_overview_report(
    farm_id: str,
    pond_id: str = None,
    cycle_id: str = None,
    date: str = None,
    user_id: str = "",
):
    """Generate overview PDF report and return JSON-serializable result data."""
    try:
        dashboard = DashboardOverview(
            farm_id=farm_id,
            pond_id=pond_id,
            cycle_id=cycle_id,
            date=date,
            user_id=user_id,
        )
        contents = async_to_sync(dashboard.download_report_pdf)()
        pdf_output = generate_pdf_report_with_data(contents)
        return {
            "status": "SUCCESS",
            "content_type": "application/pdf",
            "filename": "report_teramina.pdf",
            "data_base64": base64.b64encode(pdf_output).decode("ascii"),
        }
    except Exception as exc:
        logger.exception("Overview report generation failed: %s", exc)
        raise
