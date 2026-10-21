from typing import Any, Protocol

from ecommerce_data_platform.records import BronzeRecord, RejectedRecord
from ecommerce_data_platform.types import (
    Checkpoint,
    PipelineRun,
    PipelineStage,
    QuarantineStatus,
)


class LandingStore(Protocol):
    def persist(self, table: str, records: list[dict[str, Any]]) -> int: ...

class BronzeReader(Protocol):
    def read(self, table: str, last_ingestion_id: int | None) -> list[BronzeRecord]: ...

class CheckpointStore(Protocol):
    def get(self, stage: PipelineStage, source_table: str) -> Checkpoint | None: ...

    def set(self, stage: PipelineStage, source_table: str, checkpoint: Checkpoint) -> None: ...

class QuarantineStore(Protocol):
    def persist(
        self, table: str, records: list[RejectedRecord]
    ) -> None: ...

    def resolve(self, quarantine_id: int, status: QuarantineStatus) -> None: ...

class PipelineRunsStore(Protocol):
    def start(self, run: PipelineRun) -> None: ...

    def finish(self, run: PipelineRun) -> None: ...

    def get_consecutive_zero_row_runs(self, source_table: str) -> int: ...

    def get_rows_inspected_and_rejected_from_latest_run(
        self, source_table: str
    ) -> tuple[int, int]: ...