from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import ORDER_ITEMS_READY

from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import OrderItem


@dag(
    dag_id="ingest_order_items",
    schedule=timedelta(minutes=5),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def order_items_dag():
    @task
    def ingest_order_items():
        run_incremental_ingestion("order_items")

    @task(outlets=[ORDER_ITEMS_READY])
    def validate_order_items():
        run_bronze_validation("order_items", OrderItem)

    ingest_order_items() >> validate_order_items()

order_items_dag()