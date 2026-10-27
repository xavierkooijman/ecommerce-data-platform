from datetime import datetime, timedelta
from functools import partial

from airflow.sdk import dag, task
from callbacks import webhook_task_failure_callback

from ecommerce_data_platform.observability.checks import check_stuck_runs
from ecommerce_data_platform.observability.global_checks_runner import run_global_checks
from ecommerce_data_platform.storage.postgres import PostgresPipelineRunStore
from ecommerce_data_platform.utils.db import warehouse_connection_factory


@dag(
    dag_id="global_checks_frequent",
    schedule=timedelta(minutes=5),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def global_checks_frequent_dag():
    @task()
    def run_global_checks_frequent():
        checks = [
            partial(check_stuck_runs, PostgresPipelineRunStore(warehouse_connection_factory), 15)
        ]
        run_global_checks(checks)

    run_global_checks_frequent()

global_checks_frequent_dag()