from ecommerce_data_platform.pipeline.ingestion import EcommerceIncrementalIngestion
from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.storage.postgres import PostgresLandingStore, PostgresCheckpointStore
from unittest.mock import patch
import pytest

def test_ingestion_loads_records_and_updates_checkpoint(postgres_source_conn, postgres_warehouse_conn):
    extractor = PostgresIncrementalExtractor(
        postgres_source_conn
    )

    landing_store = PostgresLandingStore(
        postgres_warehouse_conn
    )

    checkpoint_store = PostgresCheckpointStore(
        postgres_warehouse_conn
    )

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        postgres_warehouse_conn,
    )

    ingestion.run("customers")
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bronze.customers")

        assert cur.fetchone()[0] == 4

    watermark = checkpoint_store.get("customers")

    assert watermark is not None

def test_ingestion_rolls_back_when_checkpoint_update_fails(
    postgres_source_conn,
    postgres_warehouse_conn,
):
    extractor = PostgresIncrementalExtractor(
        postgres_source_conn
    )

    landing_store = PostgresLandingStore(
        postgres_warehouse_conn
    )

    checkpoint_store = PostgresCheckpointStore(
        postgres_warehouse_conn
    )

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        postgres_warehouse_conn,
    )

    previous_watermark = checkpoint_store.get("customers")

    with patch.object(
        checkpoint_store,
        "set",
        side_effect=RuntimeError("simulated crash before checkpoint write"),
    ):
        with pytest.raises(RuntimeError):
            ingestion.run("customers")

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM bronze.customers"
        )

        assert cur.fetchone()[0] == 0

    assert checkpoint_store.get("customers") == previous_watermark
    