from pydantic import BaseModel

from ecommerce_data_platform.storage.postgres import (
    PostgresBronzeReader,
    PostgresCheckpointStore,
    PostgresQuarantineStore,
)
from ecommerce_data_platform.types import PipelineStage
from ecommerce_data_platform.utils.db import warehouse_connection
from ecommerce_data_platform.validation.validator import validate


def run_bronze_validation(table: str, model:type[BaseModel]) -> None:
    with warehouse_connection() as warehouse_conn:
        checkpoint_store = PostgresCheckpointStore(warehouse_conn)
        checkpoint = checkpoint_store.get(PipelineStage.VALIDATION, table)
        warehouse_conn.commit()

        if checkpoint is not None and not isinstance(checkpoint, int):
            raise TypeError(
                "Bronze validation checkpoint must be an integer"
            )  

        last_id = checkpoint

        records = PostgresBronzeReader(warehouse_conn).read(table, last_id)
        if not records:
            return
        
        rejected = validate(model, records)

        with warehouse_conn.transaction():
            PostgresQuarantineStore(warehouse_conn).persist(table, rejected)
            new_checkpoint = max(record.ingestion_id for record in records)
            checkpoint_store.set(PipelineStage.VALIDATION, table, new_checkpoint)