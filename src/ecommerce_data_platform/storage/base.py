from datetime import datetime
from typing import Any, Protocol


class LandingStore(Protocol):
    def persist(self, table: str, records: list[dict[str, Any]]) -> int: ...

class CheckpointStore(Protocol):
    def get(self, pipeline_name: str) -> datetime | None: ...

    def set(self, pipeline_name: str, watermark: datetime) -> None: ...