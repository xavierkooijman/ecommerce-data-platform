from collections.abc import Callable
from dataclasses import dataclass

from ecommerce_data_platform.storage.base import PipelineRunsStore
from ecommerce_data_platform.types import SourceTable


@dataclass(frozen=True)
class TriggeredCheck:
    name: str
    source_table: SourceTable
    observed_value: int | float
    threshold: int | float

@dataclass(frozen=True)
class CheckConfig[T : int | float]:
    check: Callable[
        [PipelineRunsStore, SourceTable, T],
        TriggeredCheck | None,
    ]
    threshold: T

class CheckThresholdExceeded(Exception):
    def __init__(self, checks: list[TriggeredCheck]) -> None:
        self.checks = checks

        details = "; ".join(
            f"{check.name} for {check.source_table}: "
            f"observed={check.observed_value}, "
            f"threshold={check.threshold}"
            for check in checks
        )

        super().__init__(f"Pipeline checks triggered: {details}")