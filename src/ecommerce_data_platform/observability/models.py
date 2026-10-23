from collections.abc import Callable
from dataclasses import dataclass

from ecommerce_data_platform.models import DataSource
from ecommerce_data_platform.storage.base import PipelineRunStore


@dataclass(frozen=True)
class TriggeredCheck:
    name: str
    data_source: DataSource
    observed_value: int | float
    threshold: int | float

@dataclass(frozen=True)
class CheckConfig[T : int | float]:
    check: Callable[
        [PipelineRunStore, DataSource, T],
        TriggeredCheck | None,
    ]
    threshold: T

class CheckThresholdExceeded(Exception):
    def __init__(self, checks: list[TriggeredCheck]) -> None:
        self.checks = checks

        details = "; ".join(
            f"{check.name} for {check.data_source.resource} from "
            f"{check.data_source.source_system}: "
            f"observed={check.observed_value}, "
            f"threshold={check.threshold}"
            for check in checks
        )

        super().__init__(f"Pipeline checks triggered: {details}")