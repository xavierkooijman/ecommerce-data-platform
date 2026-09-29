from typing import Protocol, Any
from datetime import datetime

class LandingStore(Protocol):
    def persist(table: str, records: list[dict[str, Any]]) -> int: ...

class CheckpointStore(Protocol):
    def get(pipeline_name: str) -> datetime | None: ...

    def set(pipeline_name: str, watermark: datetime) -> None: ...