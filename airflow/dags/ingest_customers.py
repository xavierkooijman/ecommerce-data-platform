from datetime import datetime, timedelta

from airflow.sdk import Asset, dag, task

from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import Customer

CUSTOMERS_READY = Asset("customers_ready")

@dag(
    dag_id="ingest_customers",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def customers_dag():
    @task
    def ingest_customers():
        run_incremental_ingestion("customers")

    @task(outlets=[CUSTOMERS_READY])
    def validate_customers():
        run_bronze_validation("customers", Customer)

    ingest_customers() >> validate_customers()

customers_dag()