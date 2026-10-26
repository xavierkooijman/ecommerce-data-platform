from ecommerce_data_platform.models import DataSource, Resource, SourceSystem
from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate_percentage,
)
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    SourceCheckConfig,
    TriggeredCheck,
)
from ecommerce_data_platform.storage.base import PipelineRunStore

SOURCE_CHECKS_CONFIG: dict[DataSource, list[SourceCheckConfig]] = {
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.CUSTOMERS): [
        SourceCheckConfig(check_consecutive_zero_row_runs, threshold=3),
        SourceCheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.PRODUCTS): [
        SourceCheckConfig(check_consecutive_zero_row_runs, threshold=3),
        SourceCheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.ORDERS): [
        SourceCheckConfig(check_consecutive_zero_row_runs, threshold=3),
        SourceCheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.ORDER_ITEMS): [
        SourceCheckConfig(check_consecutive_zero_row_runs, threshold=3),
        SourceCheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.SHIPMENTS): [
        SourceCheckConfig(check_consecutive_zero_row_runs, threshold=3),
        SourceCheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
}

def run_source_checks(data_source: DataSource, store: PipelineRunStore) -> None:
    triggered: list[TriggeredCheck] = []

    for config in SOURCE_CHECKS_CONFIG[data_source]:
        alert = config.check(
            store, data_source, config.threshold
        )

        if alert:
            triggered.append(alert)

    if triggered:
        raise CheckThresholdExceeded(triggered)