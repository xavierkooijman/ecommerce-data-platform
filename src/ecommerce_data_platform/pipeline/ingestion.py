from datetime import datetime

from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.storage.postgres import (
    PostgresCheckpointStore,
    PostgresLandingStore,
    PostgresPipelineRunsStore,
)
from ecommerce_data_platform.types import ExecutionContext, PipelineStage
from ecommerce_data_platform.utils.db import source_connection, warehouse_connection


def run_incremental_ingestion(table: str, execution_context: ExecutionContext) -> None:

    with warehouse_connection() as warehouse_conn:
        with PipelineRunTracker(
            stage=PipelineStage.INGESTION,
            store=PostgresPipelineRunsStore(warehouse_conn),
            source_table=table,
            execution_context=execution_context,
        ) as run:
            checkpoint_store = PostgresCheckpointStore(warehouse_conn)
            checkpoint = checkpoint_store.get(PipelineStage.INGESTION, table)

            if checkpoint is not None and not isinstance(checkpoint, datetime):
                raise TypeError(
                    "Incremental ingestion checkpoint must be a datetime"
                )

            watermark = checkpoint

            with source_connection() as source_conn:
                records = PostgresIncrementalExtractor(source_conn).extract(table, watermark)

            run.rows_extracted = len(records)

            if not records:
                return

            with warehouse_conn.transaction():
                PostgresLandingStore(warehouse_conn).persist(table, records)
                new_checkpoint = max(record["updated_at"] for record in records)
                run.watermark = new_checkpoint
                checkpoint_store.set(PipelineStage.INGESTION, table, new_checkpoint)

            run.rows_loaded = len(records)

