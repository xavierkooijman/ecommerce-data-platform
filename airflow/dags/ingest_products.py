from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import PRODUCTS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.observability.checks_runner import run_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.types import SourceTable
from ecommerce_data_platform.validation.models import Product


@dag(
    dag_id="ingest_products",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def products_dag():
    @task
    def ingest_products():
        run_incremental_ingestion(SourceTable.PRODUCTS, get_execution_context())

    @task
    def validate_products():
        run_bronze_validation(SourceTable.PRODUCTS, Product, get_execution_context())

    @task(outlets=[PRODUCTS_READY])
    def check_product_alerts():
        run_checks(SourceTable.PRODUCTS)

    ingest_products() >> validate_products() >> check_product_alerts()

products_dag()


