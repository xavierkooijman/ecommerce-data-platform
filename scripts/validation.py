
import argparse

from ecommerce_data_platform.models import (
    DataSource,
    PipelineStage,
    Resource,
    SourceSystem,
)
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.storage.postgres import (
    PostgresBronzeStore,
    PostgresCheckpointStore,
    PostgresPipelineRunStore,
    PostgresQuarantineStore,
)
from ecommerce_data_platform.utils.db import (
    warehouse_connection_factory,
)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run bronze validation')
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

    run_bronze_validation(
        data_source=data_source,
        bronze_store=PostgresBronzeStore(
            warehouse_connection_factory
        ),
        checkpoint_store=PostgresCheckpointStore(
            warehouse_connection_factory
        ),
        quarantine_store=PostgresQuarantineStore(
            warehouse_connection_factory
        ),
        run_tracker=PipelineRunTracker(
            stage=PipelineStage.VALIDATION,
            store=PostgresPipelineRunStore(
                warehouse_connection_factory
            ),
            data_source=data_source,
        ),
    )

    print(f'Validation completed successfully: {data_source}')

if __name__ == '__main__':
    main()