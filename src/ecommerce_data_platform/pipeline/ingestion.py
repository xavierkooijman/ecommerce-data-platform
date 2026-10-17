from datetime import datetime

from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.storage.postgres import PostgresCheckpointStore, PostgresLandingStore
from ecommerce_data_platform.types import PipelineStage
from ecommerce_data_platform.utils.db import source_connection, warehouse_connection


def run_incremental_ingestion(table: str) -> None:

    with warehouse_connection() as warehouse_conn:
        checkpoint_store = PostgresCheckpointStore(warehouse_conn)
        checkpoint = checkpoint_store.get(PipelineStage.INGESTION, table)
        warehouse_conn.commit()

        if checkpoint is not None and not isinstance(checkpoint, datetime):
            raise TypeError(
                "Incremental ingestion checkpoint must be a datetime"
            )

        watermark = checkpoint

        with source_connection() as source_conn:
            records = PostgresIncrementalExtractor(source_conn).extract(table, watermark)

        if not records:
            return

        with warehouse_conn.transaction():
            PostgresLandingStore(warehouse_conn).persist(table, records)
            new_checkpoint = max(record["updated_at"] for record in records)
            checkpoint_store.set(PipelineStage.INGESTION, table, new_checkpoint)


