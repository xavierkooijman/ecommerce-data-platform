from typing import Any, Protocol

from ecommerce_data_platform.types import Checkpoint


class LandingStore(Protocol):
    def persist(self, table: str, records: list[dict[str, Any]]) -> int: ...

class CheckpointStore(Protocol):
    def get(self, stage: str, source_table: str) -> Checkpoint | None: ...

    def set(self, stage: str, source_table: str, checkpoint: Checkpoint) -> None: ...