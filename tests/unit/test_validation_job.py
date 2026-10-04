from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ecommerce_data_platform.pipeline.validation import BronzeValidationJob
from ecommerce_data_platform.records import BronzeRecord


def test_run_returns_when_no_records_found():
    reader = Mock()
    reader.read.return_value = []

    quarantine_store = Mock()
    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    warehouse_conn = Mock()

    job = BronzeValidationJob(
        reader=reader,
        quarantine_store=quarantine_store,
        checkpoint_store=checkpoint_store,
        warehouse_conn=warehouse_conn,
    )

    job.run("customers", Mock())

    checkpoint_store.get.assert_called_once_with("validation", "customers")
    reader.read.assert_called_once_with("customers", None)      

    quarantine_store.persist.assert_not_called()
    checkpoint_store.set.assert_not_called()
    warehouse_conn.commit.assert_not_called()

def test_run_raises_when_checkpoint_is_not_integer():
    reader = Mock()

    checkpoint_store = Mock()
    checkpoint_store.get.return_value = datetime.now(UTC)

    job = BronzeValidationJob(
        reader=reader,
        quarantine_store=Mock(),
        checkpoint_store=checkpoint_store,
        warehouse_conn=Mock(),
    )

    with pytest.raises(TypeError):
        job.run("customers", Mock())

def test_run_rolls_back_when_quarantine_store_fails():
    reader = Mock()
    reader.read.return_value = [
        BronzeRecord(
            ingestion_id=1,
            payload={},
        )
    ]

    quarantine_store = Mock()
    quarantine_store.persist.side_effect = RuntimeError()

    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None

    warehouse_conn = Mock()

    job = BronzeValidationJob(
        reader=reader,
        quarantine_store=quarantine_store,
        checkpoint_store=checkpoint_store,
        warehouse_conn=warehouse_conn,
    )

    with pytest.raises(RuntimeError):
        job.run("customers", Mock())

    warehouse_conn.rollback.assert_called_once()
    warehouse_conn.commit.assert_not_called()


def test_run_rolls_back_when_checkpoint_update_fails():
    reader = Mock()
    reader.read.return_value = [
        BronzeRecord(
            ingestion_id=10,
            payload={},
        )
    ]

    checkpoint_store = Mock()
    checkpoint_store.get.return_value = None
    checkpoint_store.set.side_effect = RuntimeError()

    warehouse_conn = Mock()

    job = BronzeValidationJob(
        reader=reader,
        quarantine_store=Mock(),
        checkpoint_store=checkpoint_store,
        warehouse_conn=warehouse_conn,
    )

    with pytest.raises(RuntimeError):
        job.run("customers", Mock())

    warehouse_conn.rollback.assert_called_once()
    warehouse_conn.commit.assert_not_called()