import os
from datetime import datetime

from airflow.sdk import dag, task
from assets import SHIPMENTS_READY

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_shipments",
    schedule=SHIPMENTS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def transform_shipments():

    @task.bash(cwd=DBT_DIR)
    def build():
        return (
            "dbt build "
            "--select shipments"
        )

    build()

transform_shipments()