from datetime import datetime
from typing import Any, Protocol

from ecommerce_data_platform.records import BronzeRecord, RejectedRecord


class LandingStore(Protocol):
    def persist(self, table: str, records: list[dict[str, Any]]) -> int: ...

class BronzeReader(Protocol):
    def read(self, table: str, last_ingestion_id: int | None) -> list[BronzeRecord]: ...

class CheckpointStore(Protocol):
    def get(self, pipeline_name: str) -> datetime | None: ...

    def set(self, pipeline_name: str, watermark: datetime) -> None: ...

class QuarantineStore(Protocol):
    def persist(
        self, table: str, records: list[RejectedRecord]
    ) -> None: ...

    def resolve(self, quarantine_id: int, status: str) -> None: ...