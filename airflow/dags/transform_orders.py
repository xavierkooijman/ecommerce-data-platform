import os
from datetime import datetime

from airflow.sdk import dag, task
from assets import ECOMMERCE_DB_ORDER_ITEMS_READY, ECOMMERCE_DB_ORDERS_READY
from callbacks import webhook_task_failure_callback

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_orders",
    schedule=ECOMMERCE_DB_ORDERS_READY & ECOMMERCE_DB_ORDER_ITEMS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback
)
def transform_orders():

    @task.bash(cwd=DBT_DIR)
    def build_orders():
        return (
            "dbt build "
            "--select orders order_items fct_orders fct_order_items"
        )

    build_orders()

transform_orders()