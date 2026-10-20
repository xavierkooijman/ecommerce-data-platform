from ecommerce_data_platform.observability.checks_config import CHECK_CONFIG
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    TriggeredCheck,
)
from ecommerce_data_platform.storage.postgres import PostgresPipelineRunsStore
from ecommerce_data_platform.types import SourceTable


def run_checks(source_table: SourceTable) -> None:
    triggered: list[TriggeredCheck] = []

    for config in CHECK_CONFIG[source_table]:
        alert = config.check(PostgresPipelineRunsStore(), source_table, config.threshold)

        if alert:
            triggered.append(alert)

    if triggered:
        raise CheckThresholdExceeded(triggered)