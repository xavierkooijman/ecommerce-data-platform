from datetime import datetime, timedelta
from functools import partial

from airflow.sdk import dag, task
from callbacks import webhook_task_failure_callback

from ecommerce_data_platform.observability.checks import check_oldest_open_quarantine_age_hours
from ecommerce_data_platform.observability.global_checks_runner import run_global_checks


@dag(
    dag_id="global_checks_daily",
    schedule=timedelta(days=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def global_checks_daily_dag():
    @task()
    def run_global_checks_daily():
        checks = [
            partial(check_oldest_open_quarantine_age_hours(168.0))
        ]
        run_global_checks(checks)

    run_global_checks_daily()

global_checks_daily_dag()