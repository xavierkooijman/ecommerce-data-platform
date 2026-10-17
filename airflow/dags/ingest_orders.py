from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import ORDERS_READY

from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import Order


@dag(
    dag_id="ingest_orders",
    schedule=timedelta(minutes=5),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def orders_dag():
    @task
    def ingest_orders():
        run_incremental_ingestion("orders")

    @task(outlets=[ORDERS_READY])
    def validate_orders():
        run_bronze_validation("orders", Order)

    ingest_orders() >> validate_orders()

orders_dag()