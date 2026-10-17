import os
from datetime import datetime

from airflow.sdk import dag, task
from assets import CUSTOMERS_READY, PRODUCTS_READY

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_dimensions",
    schedule=CUSTOMERS_READY | PRODUCTS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def transform_dimensions():
    @task.bash(cwd=DBT_DIR)
    def build():
        return (
            "dbt build "
            "--select customers products customers_snapshot dim_customer dim_product "
            "--indirect-selection cautious"
        )

    build()

transform_dimensions()