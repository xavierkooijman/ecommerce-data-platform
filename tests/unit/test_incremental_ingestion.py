from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

from ecommerce_data_platform.models import PipelineStage
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion


@pytest.fixture
def setup_ingestion():
    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    bronze_store = Mock()

    records = [
        {"id": 1, "updated_at": datetime(2026, 1, 2, tzinfo=UTC)},
        {"id": 2, "updated_at": datetime(2026, 1, 3, tzinfo=UTC)},
    ]

    extractor = Mock()
    extractor.extract.return_value = records

    run = Mock()
    run_tracker = MagicMock()
    run_tracker.__enter__.return_value = run
    run_tracker.__exit__.return_value = False

    return {
        "checkpoint_store": checkpoint_store,
        "bronze_store": bronze_store,
        "extractor": extractor,
        "records": records,
        "run": run,
        "run_tracker": run_tracker,
    }


def test_ingestion_persists_records_and_advances_checkpoint(
    setup_ingestion, data_source, bronze_table
):
    deps = setup_ingestion

    run_incremental_ingestion(
        data_source,
        bronze_table,
        deps["extractor"],
        deps["bronze_store"],
        deps["checkpoint_store"],
        deps["run_tracker"],
    )

    deps["checkpoint_store"].get.assert_called_once_with(
        PipelineStage.INGESTION, data_source
    )
    deps["extractor"].extract.assert_called_once_with(
        data_source.resource, None
    )
    deps["bronze_store"].persist.assert_called_once_with(
        bronze_table, deps["records"]
    )
    deps["checkpoint_store"].set.assert_called_once_with(
        PipelineStage.INGESTION,
        data_source,
        datetime(2026, 1, 3, tzinfo=UTC),
    )

    assert deps["run"].rows_extracted == 2
    assert deps["run"].rows_loaded == 2
    assert deps["run"].watermark == datetime(2026, 1, 3, tzinfo=UTC)


def test_ingestion_with_no_records_does_not_advance_checkpoint(
    setup_ingestion, data_source, bronze_table
):
    deps = setup_ingestion
    deps["extractor"].extract.return_value = []

    run_incremental_ingestion(
        data_source,
        bronze_table,
        deps["extractor"],
        deps["bronze_store"],
        deps["checkpoint_store"],
        deps["run_tracker"],
    )

    deps["bronze_store"].persist.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()

    assert deps["run"].rows_extracted == 0
    assert deps["run"].rows_loaded == 0
    assert deps["run"].watermark is None


def test_ingestion_rejects_invalid_checkpoint(
    setup_ingestion, data_source, bronze_table
):
    deps = setup_ingestion
    deps["checkpoint_store"].get.return_value = "invalid"

    with pytest.raises(
        TypeError,
        match="Incremental ingestion checkpoint must be a datetime",
    ):
        run_incremental_ingestion(
            data_source,
            bronze_table,
            deps["extractor"],
            deps["bronze_store"],
            deps["checkpoint_store"],
            deps["run_tracker"],
        )

    deps["extractor"].extract.assert_not_called()
    deps["bronze_store"].persist.assert_not_called()
    deps["checkpoint_store"].set.assert_not_called()