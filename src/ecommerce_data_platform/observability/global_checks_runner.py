from collections.abc import Callable

from ecommerce_data_platform.observability.models import CheckThresholdExceeded, TriggeredCheck


def run_global_checks(
    checks: list[Callable[[], TriggeredCheck | None]]
) -> None:
    triggered: list[TriggeredCheck] = []

    for check in checks:
        alert = check()

        if alert:
            triggered.append(alert)

    if triggered:
        raise CheckThresholdExceeded(triggered)