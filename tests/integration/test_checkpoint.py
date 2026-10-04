from datetime import UTC, datetime

from ecommerce_data_platform.storage.postgres import PostgresCheckpointStore


def test_get_returns_none_when_checkpoint_does_not_exist(
    postgres_warehouse_conn,
):
    store = PostgresCheckpointStore(postgres_warehouse_conn)

    assert store.get("ingestion", "orders") is None


def test_set_and_get_timestamp_checkpoint(
    postgres_warehouse_conn,
):
    store = PostgresCheckpointStore(postgres_warehouse_conn)
    checkpoint = datetime(2026, 1, 1, tzinfo=UTC)

    store.set("ingestion", "orders", checkpoint)
    postgres_warehouse_conn.commit()

    assert store.get("ingestion", "orders") == checkpoint


def test_set_and_get_integer_checkpoint(
    postgres_warehouse_conn,
):
    store = PostgresCheckpointStore(postgres_warehouse_conn)

    store.set("validation", "orders", 123)
    postgres_warehouse_conn.commit()

    assert store.get("validation", "orders") == 123


def test_set_updates_existing_checkpoint(
    postgres_warehouse_conn,
):
    store = PostgresCheckpointStore(postgres_warehouse_conn)

    store.set("validation", "orders", 100)
    store.set("validation", "orders", 200)
    postgres_warehouse_conn.commit()

    assert store.get("validation", "orders") == 200


def test_checkpoints_are_isolated_by_stage_and_source_table(
    postgres_warehouse_conn,
):
    store = PostgresCheckpointStore(postgres_warehouse_conn)

    timestamp = datetime(2026, 1, 1, tzinfo=UTC)

    store.set("ingestion", "orders", timestamp)
    store.set("ingestion", "customers", timestamp)
    store.set("validation", "orders", 100)
    store.set("validation", "customers", 200)
    postgres_warehouse_conn.commit()

    assert store.get("ingestion", "orders") == timestamp
    assert store.get("ingestion", "customers") == timestamp
    assert store.get("validation", "orders") == 100
    assert store.get("validation", "customers") == 200