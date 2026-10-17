from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import SHIPMENTS_READY

from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.validation.models import Shipment


@dag(
    dag_id="ingest_shipments",
    schedule=timedelta(minutes=15),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def shipments_dag():
    @task
    def ingest_shipments():
        run_incremental_ingestion("shipments")

    @task(outlets=[SHIPMENTS_READY])
    def validate_shipments():
        run_bronze_validation("shipments", Shipment)

    ingest_shipments() >> validate_shipments()

shipments_dag()