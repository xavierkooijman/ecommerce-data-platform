
import argparse

from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.models import (
    DataSource,
    PipelineStage,
    Resource,
    SourceSystem,
)
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.storage.postgres import (
    PostgresBronzeStore,
    PostgresCheckpointStore,
    PostgresPipelineRunStore,
)
from ecommerce_data_platform.utils.db import (
    source_connection_factory,
    warehouse_connection_factory,
)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run incremental ingestion')
    parser.add_argument(
        '--source-system', 
        choices=[source.value for source in SourceSystem],
        required=True
    )

    parser.add_argument(
        '--resource',
        choices=[resource.value for resource in Resource],
        required=True
    )

    args = parser.parse_args()

    data_source = DataSource(
        source_system=SourceSystem(args.source_system),
        resource=Resource(args.resource),
    )

    run_incremental_ingestion(
        data_source=data_source,
        extractor=PostgresIncrementalExtractor(
            source_connection_factory
        ),
        bronze_store=PostgresBronzeStore(
            warehouse_connection_factory
        ),
        checkpoint_store=PostgresCheckpointStore(
            warehouse_connection_factory
        ),
        run_tracker=PipelineRunTracker(
            stage=PipelineStage.INGESTION,
            store=PostgresPipelineRunStore(
                warehouse_connection_factory
            ),
            data_source=data_source,
        ),
    )

    print(f'Ingestion completed successfully: {data_source}')

if __name__ == '__main__':
    main()