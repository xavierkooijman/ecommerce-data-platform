from datetime import datetime
from typing import Any, Protocol

from ecommerce_data_platform.models import Resource


class IncrementalExtractor(Protocol):
    def extract(
        self,
        resource: Resource,
        watermark: datetime | None,
        watermark_column: str = "updated_at",
    ) -> list[dict[str, Any]]: ...