from datetime import datetime, timedelta
from functools import partial

from airflow.sdk import dag, task
from callbacks import webhook_task_failure_callback

from ecommerce_data_platform.observability.checks import check_open_quarantine_count
from ecommerce_data_platform.observability.global_checks_runner import run_global_checks
from ecommerce_data_platform.storage.postgres import PostgresQuarantineStore
from ecommerce_data_platform.utils.db import warehouse_connection_factory


@dag(
    dag_id="global_checks_hourly",
    schedule=timedelta(hours=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def global_checks_hourly_dag():
    @task()
    def run_global_checks_hourly():
        checks = [
            partial(
                check_open_quarantine_count,
                PostgresQuarantineStore(warehouse_connection_factory),
                100,
            )
        ]
        run_global_checks(checks)

    run_global_checks_hourly()

global_checks_hourly_dag()