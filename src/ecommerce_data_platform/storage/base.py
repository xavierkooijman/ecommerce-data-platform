from typing import Any, Protocol

from ecommerce_data_platform.models import (
    BronzeRecord,
    BronzeTable,
    Checkpoint,
    DataSource,
    PipelineRun,
    PipelineStage,
    QuarantineStatus,
    RejectedRecord,
)


class BronzeStore(Protocol):
    def persist(self, table: BronzeTable, records: list[dict[str, Any]]) -> int: ...

    def read(self, table: BronzeTable, last_ingestion_id: int | None) -> list[BronzeRecord]: ...

class CheckpointStore(Protocol):
    def get(
        self, 
        stage: PipelineStage, 
        data_source: DataSource,
    ) -> Checkpoint | None: ...

    def set(
        self,
        stage: PipelineStage,
        data_source: DataSource,
        checkpoint: Checkpoint,
        ) -> None: ...

class QuarantineStore(Protocol):
    def persist(
        self, 
        data_source: DataSource,
        bronze_table: BronzeTable,
        records: list[RejectedRecord]
    ) -> None: ...

    def resolve(self, quarantine_id: int, status: QuarantineStatus) -> None: ...

    def get_open_quarantine_count(self) -> int: ...

    def get_oldest_open_quarantine_age_hours(self) -> int | float: ...

class PipelineRunStore(Protocol):
    def start(self, run: PipelineRun) -> None: ...

    def finish(self, run: PipelineRun) -> None: ...

    def get_consecutive_zero_row_runs(self, data_source: DataSource) -> int: ...

    def get_rows_inspected_and_rejected_from_latest_run(
        self,         
        data_source: DataSource,
    ) -> tuple[int, int]: ...