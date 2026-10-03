from typing import Any, Protocol

from ecommerce_data_platform.records import BronzeRecord, RejectedRecord
from ecommerce_data_platform.types import Checkpoint


class LandingStore(Protocol):
    def persist(self, table: str, records: list[dict[str, Any]]) -> int: ...

class BronzeReader(Protocol):
    def read(self, table: str, last_ingestion_id: int | None) -> list[BronzeRecord]: ...

class CheckpointStore(Protocol):
    def get(self, stage: str, source_table: str) -> Checkpoint | None: ...

    def set(self, stage: str, source_table: str, checkpoint: Checkpoint) -> None: ...

class QuarantineStore(Protocol):
    def persist(
        self, table: str, records: list[RejectedRecord]
    ) -> None: ...

    def resolve(self, quarantine_id: int, status: str) -> None: ...