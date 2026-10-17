import os
from datetime import datetime

from airflow.sdk import dag, task
from ingest_order_items import ORDER_ITEMS_READY
from ingest_orders import ORDERS_READY

DBT_DIR = os.getenv("DBT_DIR", "/opt/airflow/ecommerce_data_platform/dbt")

@dag(
    dag_id="transform_orders",
    schedule=ORDERS_READY & ORDER_ITEMS_READY,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
)
def transform_orders():

    @task.bash(cwd=DBT_DIR)
    def build():
        return (
            "dbt build "
            "--select orders order_items fct_orders fct_order_items"
        )

    build()

transform_orders()