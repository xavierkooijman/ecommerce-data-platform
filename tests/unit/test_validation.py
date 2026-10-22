from unittest.mock import MagicMock, Mock

import pytest
from pydantic import BaseModel

from ecommerce_data_platform.models import PipelineStage
from ecommerce_data_platform.pipeline.validation import run_bronze_validation


class CustomerModel(BaseModel):
    id: int

@pytest.fixture
def setup_validation(monkeypatch):
    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    records = [
        Mock(ingestion_id=1, payload={"id": 1}),
        Mock(ingestion_id=2, payload={"id": 2}),
    ]
    rejected = [records[1]]

    bronze_store = Mock()
    bronze_store.read.return_value = records

    quarantine_store = Mock()

    run = Mock()
    run_tracker = MagicMock()
    run_tracker.__enter__.return_value = run
    run_tracker.__exit__.return_value = False

    monkeypatch.setattr(
        "ecommerce_data_platform.pipeline.validation.validate",
        Mock(return_value=rejected),
    )

    return {
        "checkpoint_store": checkpoint_store,
        "bronze_store": bronze_store,
        "quarantine_store": quarantine_store,
        "records": records,
        "rejected": rejected,
        "run": run,
        "run_tracker": run_tracker,
    }


def test_validation_quarantines_rejected_records_and_advances_checkpoint(
    setup_validation, data_source, bronze_table
):
    deps = setup_validation

    run_bronze_validation(
        data_source,
        bronze_table,
        CustomerModel,
        deps["bronze_store"],
        deps["checkpoint_store"],
        deps["quarantine_store"],
        deps["run_tracker"],
    )

    deps["checkpoint_store"].get.assert_called_once_with(
        PipelineStage.VALIDATION, data_source
    )
    deps["bronze_store"].read.assert_called_once_with(bronze_table, None)
    deps["quarantine_store"].persist.assert_called_once_with(
        data_source, bronze_table, deps["rejected"]
    )
    deps["checkpoint_store"].set.assert_called_once_with(
        PipelineStage.VALIDATION, data_source, 2
    )

    assert deps["run"].rows_inspected == 2
    assert deps["run"].rows_rejected == 1


def test_validation_with_no_records_does_not_advance_checkpoint(
    setup_validation, data_source, bronze_table
):
    deps = setup_validation
    deps["bronze_store"].read.return_value = []

    run_bronze_validation(
        data_source,
        bronze_table,
        CustomerModel,
        deps["bronze_store"],
        deps["checkpoint_store"],
        deps["quarantine_store"],
        deps["run_tracker"],
    )

    deps["quarantine_store"].persist.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()

    assert deps["run"].rows_inspected == 0
    assert deps["run"].rows_rejected == 0


def test_validation_rejects_invalid_checkpoint(
    setup_validation, data_source, bronze_table
):
    deps = setup_validation
    deps["checkpoint_store"].get.return_value = "invalid"

    with pytest.raises(
        TypeError,
        match="Bronze validation checkpoint must be an integer",
    ):
        run_bronze_validation(
            data_source,
            bronze_table,
            CustomerModel,
            deps["bronze_store"],
            deps["checkpoint_store"],
            deps["quarantine_store"],
            deps["run_tracker"],
        )

    deps["bronze_store"].read.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()