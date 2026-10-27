
import logging
import os

from ecommerce_data_platform.observability.alert import (
    send_webhook_alert,
)

logger = logging.getLogger(__name__)


def webhook_task_failure_callback(context: dict) -> None:
    ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")

    if not ALERT_WEBHOOK_URL:
        logger.warning("ALERT_WEBHOOK_URL is not set. Skipping webhook alert.")
        return

    ti = context.get("ti")
    exception = context.get("exception")

    message = (
        "*Airflow task failed*\n"
        f"*DAG:* {ti.dag_id if ti else 'unknown'}\n"
        f"*Task:* {ti.task_id if ti else 'unknown'}\n"
        f"*Run:* {context.get('run_id', 'unknown')}\n"
        f"*Error:* {exception or 'Unknown error'}"
    )

    try:
        send_webhook_alert(ALERT_WEBHOOK_URL, message)
    except Exception:
        logger.exception("Failed to send webhook alert.")
