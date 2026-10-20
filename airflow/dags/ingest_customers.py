from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import CUSTOMERS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.observability.checks_runner import run_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import Customer, SourceTable


@dag(
    dag_id="ingest_customers",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def customers_dag():
    @task
    def ingest_customers():
        run_incremental_ingestion(SourceTable.CUSTOMERS, get_execution_context())

    @task(outlets=[CUSTOMERS_READY])
    def validate_customers():
        run_bronze_validation(SourceTable.CUSTOMERS, Customer, get_execution_context())

    @task
    def check_alerts():
        run_checks(SourceTable.CUSTOMERS)

    ingest_customers() >> validate_customers() >> check_alerts()

customers_dag()