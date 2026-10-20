from contextlib import nullcontext
from unittest.mock import MagicMock, Mock

import pytest

import ecommerce_data_platform.pipeline.validation as validation
from ecommerce_data_platform.types import ExecutionContext


@pytest.fixture
def execution_context():
    return ExecutionContext(
        run_id="test-run",
        task_id="validate_customers",
    )


@pytest.fixture
def setup_validation(monkeypatch):
    conn = MagicMock()
    conn.transaction.return_value = nullcontext()

    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    records = [
        Mock(ingestion_id=1, payload={"id": 1}),
        Mock(ingestion_id=2, payload={"id": 2}),
    ]
    rejected = [records[1]]

    reader = Mock()
    reader.read.return_value = records

    quarantine_store = Mock()

    run = Mock()
    tracker = Mock()
    tracker.__enter__ = Mock(return_value=run)
    tracker.__exit__ = Mock(return_value=False)

    monkeypatch.setattr(
        validation,
        "warehouse_connection",
        lambda: conn,
    )
    monkeypatch.setattr(
        validation,
        "PostgresCheckpointStore",
        lambda connection: checkpoint_store,
    )
    monkeypatch.setattr(
        validation,
        "PostgresBronzeReader",
        lambda: reader,
    )
    monkeypatch.setattr(
        validation,
        "PostgresQuarantineStore",
        lambda connection: quarantine_store,
    )
    monkeypatch.setattr(
        validation,
        "PostgresPipelineRunsStore",
        Mock,
    )
    monkeypatch.setattr(
        validation,
        "PipelineRunTracker",
        lambda **kwargs: tracker,
    )
    monkeypatch.setattr(
        validation,
        "validate",
        Mock(return_value=rejected),
    )

    return {
        "conn": conn,
        "checkpoint_store": checkpoint_store,
        "reader": reader,
        "quarantine_store": quarantine_store,
        "records": records,
        "rejected": rejected,
        "run": run,
    }


def test_validation_quarantines_rejected_records_and_advances_checkpoint(
    setup_validation,
    execution_context,
):
    deps = setup_validation

    validation.run_bronze_validation(
        "customers",
        Mock(),
        execution_context,
    )

    deps["reader"].read.assert_called_once_with("customers", None)
    deps["quarantine_store"].persist.assert_called_once_with(
        "customers",
        deps["rejected"],
    )
    deps["checkpoint_store"].set.assert_called_once_with(
        validation.PipelineStage.VALIDATION,
        "customers",
        2,
    )

    assert deps["run"].rows_inspected == 2
    assert deps["run"].rows_rejected == 1


def test_validation_with_no_records_does_not_advance_checkpoint(
    setup_validation,
    execution_context,
):
    deps = setup_validation
    deps["reader"].read.return_value = []

    validation.run_bronze_validation(
        "customers",
        Mock(),
        execution_context,
    )

    deps["quarantine_store"].persist.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()

    assert deps["run"].rows_inspected == 0
    assert deps["run"].rows_rejected == 0


def test_validation_rejects_invalid_checkpoint(
    setup_validation,
    execution_context,
):
    deps = setup_validation
    deps["checkpoint_store"].get.return_value = "invalid"

    with pytest.raises(TypeError, match="checkpoint must be an integer"):
        validation.run_bronze_validation(
            "customers",
            Mock(),
            execution_context,
        )

    deps["reader"].read.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()