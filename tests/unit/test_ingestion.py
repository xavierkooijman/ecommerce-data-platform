
from datetime import datetime
from unittest.mock import Mock

import pytest

from ecommerce_data_platform.pipeline.ingestion import EcommerceIncrementalIngestion


def test_run_persists_records_and_updates_checkpoint():
    extractor = Mock()
    landing_store = Mock()
    checkpoint_store = Mock()
    warehouse_conn = Mock()

    checkpoint_store.get.return_value = None

    records = [
        {"updated_at": datetime(2026, 1, 1)},
        {"updated_at": datetime(2026, 1, 2)},
    ]
    extractor.extract.return_value = records

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        warehouse_conn,
    )

    ingestion.run("customers")

    extractor.extract.assert_called_once_with("customers", None)
    landing_store.persist.assert_called_once_with("customers", records)
    checkpoint_store.set.assert_called_once_with(
        "ingestion",
        "customers",
        datetime(2026, 1, 2),
    )
    warehouse_conn.commit.assert_called_once()


def test_run_rolls_back_when_checkpoint_update_fails():
    extractor = Mock()
    landing_store = Mock()
    checkpoint_store = Mock()
    warehouse_conn = Mock()

    checkpoint_store.get.return_value = None
    extractor.extract.return_value = [
        {"updated_at": datetime(2026, 1, 1)}
    ]

    checkpoint_store.set.side_effect = RuntimeError("database error")

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        warehouse_conn,
    )

    with pytest.raises(RuntimeError):
        ingestion.run("customers")

    landing_store.persist.assert_called_once()
    warehouse_conn.commit.assert_not_called()
    warehouse_conn.rollback.assert_called_once()


def test_run_returns_when_no_records_found():
    extractor = Mock()
    landing_store = Mock()
    checkpoint_store = Mock()
    warehouse_conn = Mock()

    checkpoint_store.get.return_value = None
    extractor.extract.return_value = []

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        warehouse_conn,
    )

    ingestion.run("customers")

    landing_store.persist.assert_not_called()
    checkpoint_store.set.assert_not_called()
    warehouse_conn.commit.assert_not_called()
    warehouse_conn.rollback.assert_not_called()