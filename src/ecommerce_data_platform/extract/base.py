from typing import Protocol, Any
from datetime import datetime

class IncrementalExtractor(Protocol):
    def extract(table: str, watermark: datetime | None, watermark_column: str = "updated_at") -> list[dict[str, Any]]: ...