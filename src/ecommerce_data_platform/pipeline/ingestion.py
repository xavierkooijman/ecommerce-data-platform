from datetime import datetime

from ecommerce_data_platform.extract.base import IncrementalExtractor
from ecommerce_data_platform.models import BronzeTable, DataSource, PipelineStage
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.storage.base import (
    BronzeStore,
    CheckpointStore,
)


def run_incremental_ingestion(
    data_source: DataSource,
    bronze_table: BronzeTable,
    extractor: IncrementalExtractor,
    bronze_store: BronzeStore,
    checkpoint_store: CheckpointStore,
    run_tracker: PipelineRunTracker
) -> None:
    with run_tracker as run:
        checkpoint = checkpoint_store.get(PipelineStage.INGESTION, data_source)

        if checkpoint is not None and not isinstance(checkpoint, datetime):
            raise TypeError(
                "Incremental ingestion checkpoint must be a datetime"
            )

        watermark = checkpoint

        records = extractor.extract(data_source.resource, watermark)

        run.rows_extracted = len(records)
        run.rows_loaded = 0
        run.watermark = watermark

        if not records:
            return

        bronze_store.persist(bronze_table, records)
        new_checkpoint = max(record["updated_at"] for record in records)
        checkpoint_store.set(PipelineStage.INGESTION, data_source, new_checkpoint)
            
        run.watermark = new_checkpoint
        run.rows_loaded = len(records)