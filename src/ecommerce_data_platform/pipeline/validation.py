from pydantic import BaseModel

from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.storage.postgres import (
    PostgresBronzeReader,
    PostgresCheckpointStore,
    PostgresPipelineRunsStore,
    PostgresQuarantineStore,
)
from ecommerce_data_platform.types import ExecutionContext, PipelineStage
from ecommerce_data_platform.utils.db import warehouse_connection
from ecommerce_data_platform.validation.validator import validate


def run_bronze_validation(
    table: str, model: type[BaseModel], execution_context: ExecutionContext
) -> None:
    with PipelineRunTracker(
        stage=PipelineStage.VALIDATION,
        store=PostgresPipelineRunsStore(),
        source_table=table,
        execution_context=execution_context,
    ) as run:
        with warehouse_connection() as warehouse_conn:
            checkpoint_store = PostgresCheckpointStore(warehouse_conn)
            checkpoint = checkpoint_store.get(PipelineStage.VALIDATION, table)

            if checkpoint is not None and not isinstance(checkpoint, int):
                raise TypeError(
                    "Bronze validation checkpoint must be an integer"
                )  

            last_id = checkpoint

            records = PostgresBronzeReader().read(table, last_id)
            run.rows_inspected = len(records)
            if not records:
                return
            
            rejected = validate(model, records)
            run.rows_rejected = len(rejected)

            with warehouse_conn.transaction():
                PostgresQuarantineStore(warehouse_conn).persist(table, rejected)
                new_checkpoint = max(record.ingestion_id for record in records)
                checkpoint_store.set(PipelineStage.VALIDATION, table, new_checkpoint)