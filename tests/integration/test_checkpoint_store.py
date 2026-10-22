from datetime import UTC, datetime

from ecommerce_data_platform.models import PipelineStage
from ecommerce_data_platform.storage.postgres import PostgresCheckpointStore


def test_get_returns_none_when_checkpoint_does_not_exist(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresCheckpointStore(warehouse_connection_factory)

    assert store.get(PipelineStage.INGESTION, data_source) is None


def test_set_and_get_timestamp_checkpoint(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresCheckpointStore(warehouse_connection_factory)
    checkpoint = datetime(2026, 1, 1, tzinfo=UTC)

    store.set(PipelineStage.INGESTION, data_source, checkpoint)

    assert store.get(PipelineStage.INGESTION, data_source) == checkpoint


def test_set_and_get_integer_checkpoint(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresCheckpointStore(warehouse_connection_factory)

    store.set(PipelineStage.VALIDATION, data_source, 123)

    assert store.get(PipelineStage.VALIDATION, data_source) == 123


def test_set_updates_existing_checkpoint(
    warehouse_connection_factory,
    data_source,
):
    store = PostgresCheckpointStore(warehouse_connection_factory)

    store.set(PipelineStage.VALIDATION, data_source, 100)
    store.set(PipelineStage.VALIDATION, data_source, 200)

    assert store.get(PipelineStage.VALIDATION, data_source) == 200