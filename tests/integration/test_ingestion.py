from unittest.mock import patch

import pytest

from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.pipeline.ingestion import EcommerceIncrementalIngestion
from ecommerce_data_platform.storage.postgres import PostgresCheckpointStore, PostgresLandingStore


@pytest.fixture
def ingestion_components(
    postgres_source_conn,
    postgres_warehouse_conn,
):
    extractor = PostgresIncrementalExtractor(postgres_source_conn)
    landing_store = PostgresLandingStore(postgres_warehouse_conn)
    checkpoint_store = PostgresCheckpointStore(postgres_warehouse_conn)

    ingestion = EcommerceIncrementalIngestion(
        extractor,
        landing_store,
        checkpoint_store,
        postgres_warehouse_conn,
    )

    return ingestion, checkpoint_store


def test_ingestion_loads_records_and_updates_checkpoint(
    ingestion_components, postgres_warehouse_conn
):

    ingestion, checkpoint_store = ingestion_components

    ingestion.run("customers")
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bronze.customers")

        assert cur.fetchone()[0] == 4

    watermark = checkpoint_store.get("ingest", "customers")

    assert watermark is not None

def test_ingestion_rolls_back_when_checkpoint_update_fails(
    ingestion_components,
    postgres_warehouse_conn,
):

    ingestion, checkpoint_store = ingestion_components

    previous_watermark = checkpoint_store.get("ingest", "customers")

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

    assert checkpoint_store.get("ingest", "customers") == previous_watermark


@pytest.mark.parametrize(
    ("table", "expected_rows"),
    [
        ("customers", 4),
        ("products", 4),
        ("orders", 4),
        ("order_items", 6),
        ("shipments", 2),
    ],
)
def test_ingestion_lands_every_table(
    table,
    expected_rows,
    ingestion_components,
    postgres_warehouse_conn
):

    ingestion, checkpoint_store = ingestion_components
    
    ingestion.run(table)

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM bronze.{table}"
        )
        assert cur.fetchone()[0] == expected_rows

    assert checkpoint_store.get("ingest", table) is not None
    