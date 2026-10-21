from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import SHIPMENTS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.observability.checks_runner import run_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.types import SourceTable
from ecommerce_data_platform.validation.models import Shipment


@dag(
    dag_id="ingest_shipments",
    schedule=timedelta(minutes=15),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback
)
def shipments_dag():
    @task
    def ingest_shipments():
        run_incremental_ingestion(SourceTable.SHIPMENTS, get_execution_context())

    @task
    def validate_shipments():
        run_bronze_validation(SourceTable.SHIPMENTS, Shipment, get_execution_context())

    @task(outlets=[SHIPMENTS_READY])
    def check_shipment_alerts():
        run_checks(SourceTable.SHIPMENTS)

    ingest_shipments() >> validate_shipments() >> check_shipment_alerts()

shipments_dag()