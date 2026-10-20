from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import ORDERS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.observability.checks_runner import run_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.types import SourceTable
from ecommerce_data_platform.validation.models import Order


@dag(
    dag_id="ingest_orders",
    schedule=timedelta(minutes=5),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def orders_dag():
    @task
    def ingest_orders():
        run_incremental_ingestion(SourceTable.ORDERS, get_execution_context())

    @task
    def validate_orders():
        run_bronze_validation(SourceTable.ORDERS, Order, get_execution_context())

    @task(outlets=[ORDERS_READY])
    def check_order_alerts():
        run_checks(SourceTable.ORDERS)

    ingest_orders() >> validate_orders() >> check_order_alerts()

orders_dag()