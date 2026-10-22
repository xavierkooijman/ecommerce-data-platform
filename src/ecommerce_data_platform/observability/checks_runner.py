from ecommerce_data_platform.models import DataSource
from ecommerce_data_platform.observability.checks_config import CHECK_CONFIG
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    TriggeredCheck,
)
from ecommerce_data_platform.storage.base import PipelineRunStore


def run_checks(data_source: DataSource, store: PipelineRunStore) -> None:
    triggered: list[TriggeredCheck] = []

    for config in CHECK_CONFIG[data_source]:
        alert = config.check(
            store, data_source, config.threshold
        )

        if alert:
            triggered.append(alert)

    if triggered:
        raise CheckThresholdExceeded(triggered)