from datetime import datetime
from typing import Any, Protocol


class IncrementalExtractor(Protocol):
    def extract(
        self,
        table: str,
        watermark: datetime | None,
        watermark_column: str = "updated_at",
    ) -> list[dict[str, Any]]: ...