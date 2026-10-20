from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import ORDER_ITEMS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.observability.checks_runner import run_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import OrderItem, SourceTable


@dag(
    dag_id="ingest_order_items",
    schedule=timedelta(minutes=5),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def order_items_dag():
    @task
    def ingest_order_items():
        run_incremental_ingestion(SourceTable.ORDER_ITEMS, get_execution_context())

    @task(outlets=[ORDER_ITEMS_READY])
    def validate_order_items():
        run_bronze_validation(SourceTable.ORDER_ITEMS, OrderItem, get_execution_context())

    @task
    def check_alerts():
        run_checks(SourceTable.ORDER_ITEMS)

    ingest_order_items() >> validate_order_items() >> check_alerts()

order_items_dag()