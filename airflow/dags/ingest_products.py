from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import PRODUCTS_READY
from helpers import get_execution_context

from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import Product


@dag(
    dag_id="ingest_products",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def products_dag():
    @task
    def ingest_products():
        run_incremental_ingestion("products", get_execution_context())

    @task(outlets=[PRODUCTS_READY])
    def validate_products():
        run_bronze_validation("products", Product, get_execution_context())

    ingest_products() >> validate_products()

products_dag()


