from unittest.mock import Mock

import pytest

from ecommerce_data_platform.observability.pipeline_run_tracker import (
    PipelineRunTracker,
)
from ecommerce_data_platform.types import ExecutionContext


@pytest.fixture
def store():
    return Mock()


@pytest.fixture
def execution_context():
    return ExecutionContext(
        run_id="test-run",
        task_id="ingest_customers",
    )


def test_tracker_starts_and_finishes_successfully(store, execution_context):
    with PipelineRunTracker(
        stage="ingestion",
        store=store,
        source_table="customers",
        execution_context=execution_context,
    ) as run:
        run.rows_extracted = 10
        run.rows_loaded = 10

    store.start.assert_called_once_with(run)
    store.finish.assert_called_once_with(run)

    assert run.status == "success"
    assert run.rows_extracted == 10
    assert run.rows_loaded == 10
    assert run.finished_at >= run.started_at
    assert run.error_message is None


def test_tracker_records_failure_and_propagates_exception(
    store,
    execution_context,
):
    with pytest.raises(ValueError, match="bad data"):
        with PipelineRunTracker(
            stage="validation",
            store=store,
            source_table="customers",
            execution_context=execution_context,
        ) as run:
            raise ValueError("bad data")

    store.start.assert_called_once()
    store.finish.assert_called_once_with(run)

    assert run.status == "failed"
    assert run.error_message == "bad data"


def test_tracker_does_not_mask_pipeline_error_when_finish_fails(
    store,
    execution_context,
):
    store.finish.side_effect = RuntimeError("database unavailable")

    with pytest.raises(ValueError, match="original error"):
        with PipelineRunTracker(
            stage="ingestion",
            store=store,
            execution_context=execution_context,
        ):
            raise ValueError("original error")