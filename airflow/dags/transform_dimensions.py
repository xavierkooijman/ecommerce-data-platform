import os
from datetime import datetime

from airflow.sdk import dag, task
from assets import ECOMMERCE_DB_CUSTOMERS_READY, ECOMMERCE_DB_PRODUCTS_READY
from callbacks import webhook_task_failure_callback

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_dimensions",
    schedule=ECOMMERCE_DB_CUSTOMERS_READY | ECOMMERCE_DB_PRODUCTS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback
)
def transform_dimensions():
    @task.bash(cwd=DBT_DIR)
    def build_dimensions():
        return (
            "dbt build "
            "--select customers products customers_snapshot dim_customer dim_product "
            "--indirect-selection cautious"
        )

    build_dimensions()

transform_dimensions()