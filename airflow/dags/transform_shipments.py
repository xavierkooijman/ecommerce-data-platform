import os
from datetime import datetime

from airflow.sdk import dag, task
from assets import ECOMMERCE_DB_SHIPMENTS_READY
from callbacks import webhook_task_failure_callback

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_shipments",
    schedule=ECOMMERCE_DB_SHIPMENTS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback
)
def transform_shipments():

    @task.bash(cwd=DBT_DIR)
    def build_shipments():
        return (
            "dbt build "
            "--select shipments"
        )

    build_shipments()

transform_shipments()