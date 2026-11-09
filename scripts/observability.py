import argparse
from functools import partial

from ecommerce_data_platform.models import (
    DataSource,
    Resource,
    SourceSystem,
)
from ecommerce_data_platform.observability.checks import (
    check_oldest_open_quarantine_age_hours,
    check_open_quarantine_count,
    check_stuck_runs,
)
from ecommerce_data_platform.observability.global_checks_runner import run_global_checks
from ecommerce_data_platform.observability.models import CheckThresholdExceeded
from ecommerce_data_platform.observability.source_checks_runner import run_source_checks
from ecommerce_data_platform.storage.postgres import (
    PostgresPipelineRunStore,
    PostgresQuarantineStore,
)
from ecommerce_data_platform.utils.db import warehouse_connection_factory


def main() -> None:
    parser = argparse.ArgumentParser(description='Run observability checks')
    subparsers = parser.add_subparsers(dest='command', required=True)

    source_checks = subparsers.add_parser('source-checks')
    source_checks.add_argument(
        '--source-system', 
        choices=[source.value for source in SourceSystem],
        required=True
    )

    source_checks.add_argument(
        '--resource',
        choices=[resource.value for resource in Resource],
        required=True
    )

    subparsers.add_parser('global-checks')

    args = parser.parse_args()

    try:
        if args.command == 'source-checks':
            data_source = DataSource(
                source_system=SourceSystem(args.source_system),
                resource=Resource(args.resource),
            )
            run_source_checks(
                data_source=data_source,
                store=PostgresPipelineRunStore(warehouse_connection_factory)
            )
        elif args.command == 'global-checks':
            run_global_checks(
                [
                    partial(
                        check_stuck_runs,
                        PostgresPipelineRunStore(warehouse_connection_factory),
                        15
                    ),
                    partial(
                        check_open_quarantine_count,
                        PostgresQuarantineStore(warehouse_connection_factory),
                        100
                    ),
                    partial(
                        check_oldest_open_quarantine_age_hours,
                        PostgresQuarantineStore(warehouse_connection_factory),
                        168.0
                    )
                ]
            )
    except CheckThresholdExceeded as exc:
        print(exc)
        return 1

    print('All checks passed')
    return 0

if __name__ == '__main__':
    main()