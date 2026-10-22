from pydantic import BaseModel

from ecommerce_data_platform.models import BronzeTable, DataSource, PipelineStage
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.storage.base import (
    BronzeStore,
    CheckpointStore,
    QuarantineStore,
)
from ecommerce_data_platform.validation.validator import validate


def run_bronze_validation(
    data_source: DataSource,
    bronze_table: BronzeTable, 
    model: type[BaseModel],
    bronze_store: BronzeStore,
    checkpoint_store: CheckpointStore,
    quarantine_store: QuarantineStore,
    run_tracker: PipelineRunTracker
) -> None:
    with run_tracker as run:
        checkpoint = checkpoint_store.get(PipelineStage.VALIDATION, data_source)

        if checkpoint is not None and not isinstance(checkpoint, int):
            raise TypeError(
                "Bronze validation checkpoint must be an integer"
            )  

        last_id = checkpoint

        records = bronze_store.read(bronze_table, last_id)
        run.rows_inspected = len(records)
        run.rows_rejected = 0
        if not records:
            return
        
        rejected = validate(model, records)
        run.rows_rejected = len(rejected)

        quarantine_store.persist(data_source, bronze_table, rejected)
        new_checkpoint = max(record.ingestion_id for record in records)
        checkpoint_store.set(PipelineStage.VALIDATION, data_source, new_checkpoint)