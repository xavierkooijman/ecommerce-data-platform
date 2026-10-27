from datetime import UTC, datetime, timedelta

from ecommerce_data_platform.models import (
    DataSource,
    ExecutionContext,
    PipelineRun,
    PipelineRunStatus,
    PipelineStage,
)
from ecommerce_data_platform.storage.postgres import PostgresPipelineRunStore


def make_run(
    *,
    run_id: str = "run-1",
    task_id: str = "ingest_customers",
    try_number: int = 1,
    stage: PipelineStage = PipelineStage.INGESTION,
    data_source: DataSource,
    status: PipelineRunStatus = PipelineRunStatus.SUCCESS,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    rows_extracted: int = 10,
    rows_loaded: int = 10,
    rows_inspected: int = 0,
    rows_rejected: int = 0,
    watermark: datetime | None = None,
    error_message: str | None = None,
) -> PipelineRun:
    return PipelineRun(
        execution_context=ExecutionContext(
            run_id=run_id,
            task_id=task_id,
            dag_id="test_dag",
            try_number=try_number,
        ),
        stage=stage,
        data_source=data_source,
        status=status,
        started_at=started_at or datetime.now(UTC),
        finished_at=finished_at,
        rows_extracted=rows_extracted,
        rows_loaded=rows_loaded,
        rows_inspected=rows_inspected,
        rows_rejected=rows_rejected,
        watermark=watermark,
        error_message=error_message,
    )


def test_start_inserts_pipeline_run(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresPipelineRunStore(warehouse_connection_factory)
    started_at = datetime.now(UTC)

    run = make_run(
        data_source=data_source,
        started_at=started_at,
    )

    store.start(run)

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    run_id,
                    task_id,
                    dag_id,
                    try_number,
                    stage,
                    source_system,
                    resource,
                    status,
                    started_at
                FROM meta.pipeline_runs
                WHERE run_id = %s
                  AND task_id = %s
                  AND try_number = %s
                """,
                (
                    run.execution_context.run_id,
                    run.execution_context.task_id,
                    run.execution_context.try_number,
                ),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[:4] == ("run-1", "ingest_customers", "test_dag", 1)
    assert row[4] == run.stage
    assert row[5] == data_source.source_system
    assert row[6] == data_source.resource
    assert row[7] == run.status
    assert row[8] == started_at

def test_finish_updates_pipeline_run(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresPipelineRunStore(warehouse_connection_factory)

    run = make_run(
        data_source=data_source,
        finished_at=None,
    )
    store.start(run)

    finished_at = datetime.now(UTC)
    watermark = datetime(2026, 10, 25, tzinfo=UTC)

    completed_run = make_run(
        run_id=run.execution_context.run_id,
        task_id=run.execution_context.task_id,
        try_number=run.execution_context.try_number,
        stage=run.stage,
        data_source=run.data_source,
        status=PipelineRunStatus.SUCCESS,
        started_at=run.started_at,
        finished_at=finished_at,
        rows_extracted=20,
        rows_loaded=18,
        rows_inspected=20,
        rows_rejected=2,
        watermark=watermark,
        error_message=None,
    )

    store.finish(completed_run)

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    status,
                    finished_at,
                    rows_extracted,
                    rows_loaded,
                    rows_inspected,
                    rows_rejected,
                    watermark,
                    error_message
                FROM meta.pipeline_runs
                WHERE run_id = %s
                  AND task_id = %s
                  AND try_number = %s
                """,
                (
                    run.execution_context.run_id,
                    run.execution_context.task_id,
                    run.execution_context.try_number,
                ),
            )
            row = cur.fetchone()

    assert row is not None
    assert row == (
        PipelineRunStatus.SUCCESS,
        finished_at,
        20,
        18,
        20,
        2,
        watermark,
        None,
    )

def test_get_consecutive_zero_row_runs(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresPipelineRunStore(warehouse_connection_factory)

    now = datetime.now(UTC)

    runs = [
        make_run(
            run_id="run-1",
            data_source=data_source,
            started_at=now - timedelta(minutes=3),
            finished_at=now - timedelta(minutes=3),
            rows_extracted=5,
        ),
        make_run(
            run_id="run-2",
            data_source=data_source,
            started_at=now - timedelta(minutes=2),
            finished_at=now - timedelta(minutes=2),
            rows_extracted=0,
        ),
        make_run(
            run_id="run-3",
            data_source=data_source,
            started_at=now - timedelta(minutes=1),
            finished_at=now - timedelta(minutes=1),
            rows_extracted=0,
        ),
    ]

    for run in runs:
        store.start(run)
        store.finish(run)

    assert store.get_consecutive_zero_row_runs(data_source) == 2

def test_get_rows_inspected_and_rejected_from_latest_run(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresPipelineRunStore(warehouse_connection_factory)
    now = datetime.now(UTC)

    runs = [
        make_run(
            run_id="validation-1",
            task_id="validate_customers",
            stage=PipelineStage.VALIDATION,
            data_source=data_source,
            started_at=now - timedelta(minutes=2),
            finished_at=now - timedelta(minutes=2),
            rows_inspected=10,
            rows_rejected=1,
        ),
        make_run(
            run_id="validation-2",
            task_id="validate_customers",
            stage=PipelineStage.VALIDATION,
            data_source=data_source,
            started_at=now - timedelta(minutes=1),
            finished_at=now - timedelta(minutes=1),
            rows_inspected=25,
            rows_rejected=3,
        ),
    ]

    for run in runs:
        store.start(run)
        store.finish(run)

    assert (
        store.get_rows_inspected_and_rejected_from_latest_run(data_source)
        == (25, 3)
    )


def test_get_stuck_runs_count(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresPipelineRunStore(warehouse_connection_factory)
    now = datetime.now(UTC)

    old_run = make_run(
        run_id="old-run",
        data_source=data_source,
        started_at=now - timedelta(hours=2),
        finished_at=None,
    )
    recent_run = make_run(
        run_id="recent-run",
        data_source=data_source,
        started_at=now - timedelta(minutes=5),
        finished_at=None,
    )

    store.start(old_run)
    store.start(recent_run)

    assert store.get_stuck_runs_count(max_age_minutes=15) == 1