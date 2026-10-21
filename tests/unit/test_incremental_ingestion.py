from contextlib import nullcontext
from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

import ecommerce_data_platform.pipeline.ingestion as ingestion
from ecommerce_data_platform.types import ExecutionContext


@pytest.fixture
def execution_context():
    return ExecutionContext(
        run_id="test-run",
        task_id="ingest_customers",
    )


@pytest.fixture
def setup_ingestion(monkeypatch):
    conn = MagicMock()
    conn.transaction.return_value = nullcontext()

    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    landing_store = Mock()

    records = [
        {"id": 1, "updated_at": datetime(2026, 1, 2, tzinfo=UTC)},
        {"id": 2, "updated_at": datetime(2026, 1, 3, tzinfo=UTC)},
    ]

    extractor = Mock()
    extractor.extract.return_value = records

    run = Mock()
    tracker = Mock()
    tracker.__enter__ = Mock(return_value=run)
    tracker.__exit__ = Mock(return_value=False)

    monkeypatch.setattr(
        ingestion,
        "warehouse_connection",
        lambda: conn,
    )
    monkeypatch.setattr(
        ingestion,
        "PostgresCheckpointStore",
        lambda connection: checkpoint_store,
    )
    monkeypatch.setattr(
        ingestion,
        "PostgresLandingStore",
        lambda connection: landing_store,
    )
    monkeypatch.setattr(
        ingestion,
        "PostgresIncrementalExtractor",
        lambda: extractor,
    )
    monkeypatch.setattr(
        ingestion,
        "PostgresPipelineRunsStore",
        Mock,
    )
    monkeypatch.setattr(
        ingestion,
        "PipelineRunTracker",
        lambda **kwargs: tracker,
    )

    return {
        "conn": conn,
        "checkpoint_store": checkpoint_store,
        "landing_store": landing_store,
        "extractor": extractor,
        "records": records,
        "run": run,
    }


def test_ingestion_persists_records_and_advances_checkpoint(
    setup_ingestion,
    execution_context,
):
    deps = setup_ingestion

    ingestion.run_incremental_ingestion("customers", execution_context)

    deps["extractor"].extract.assert_called_once_with("customers", None)
    deps["landing_store"].persist.assert_called_once_with(
        "customers",
        deps["records"],
    )
    deps["checkpoint_store"].set.assert_called_once_with(
        ingestion.PipelineStage.INGESTION,
        "customers",
        datetime(2026, 1, 3, tzinfo=UTC),
    )

    assert deps["run"].rows_extracted == 2
    assert deps["run"].rows_loaded == 2


def test_ingestion_with_no_records_does_not_advance_checkpoint(
    setup_ingestion,
    execution_context,
):
    deps = setup_ingestion
    deps["extractor"].extract.return_value = []

    ingestion.run_incremental_ingestion("customers", execution_context)

    deps["landing_store"].persist.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()

    assert deps["run"].rows_extracted == 0
    assert deps["run"].rows_loaded == 0


def test_ingestion_rejects_invalid_checkpoint(
    setup_ingestion,
    execution_context,
):
    deps = setup_ingestion
    deps["checkpoint_store"].get.return_value = "invalid"

    with pytest.raises(TypeError, match="checkpoint must be a datetime"):
        ingestion.run_incremental_ingestion("customers", execution_context)

    deps["extractor"].extract.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()