from collections.abc import Callable
from dataclasses import dataclass

from ecommerce_data_platform.models import DataSource
from ecommerce_data_platform.storage.base import PipelineRunStore


@dataclass(frozen=True)
class TriggeredCheck:
    name: str
    observed_value: int | float
    threshold: int | float
    data_source: DataSource | None = None

@dataclass(frozen=True)
class SourceCheckConfig[T : int | float]:
    check: Callable[
        [PipelineRunStore, DataSource, T],
        TriggeredCheck | None,
    ]
    threshold: T

class CheckThresholdExceeded(Exception):
    def __init__(self, triggered_checks: list[TriggeredCheck]) -> None:
        self.triggered_checks = triggered_checks

        details = "; ".join(
            self._format_check(check)
            for check in triggered_checks
        )

        super().__init__(f"Pipeline checks triggered: {details}")

    @staticmethod
    def _format_check(check: TriggeredCheck) -> str:
        source = check.data_source
        source_details = ""

        if source is not None:
            source_details = (
                f" for {source.resource} from {source.source_system}"
            )

        return (
            f"{check.name}{source_details}: "
            f"observed={check.observed_value}, "
            f"threshold={check.threshold}"
        )