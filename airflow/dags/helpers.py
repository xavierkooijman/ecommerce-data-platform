from airflow.sdk import get_current_context

from ecommerce_data_platform.models import ExecutionContext


def get_execution_context() -> ExecutionContext:
    context = get_current_context()
    ti = context["ti"]

    return ExecutionContext(
        run_id=context["run_id"],
        task_id=ti.task_id,
        dag_id=context["dag"].dag_id,
        try_number=ti.try_number,
    )