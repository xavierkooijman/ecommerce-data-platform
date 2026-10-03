from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BronzeRecord:
    ingestion_id: int
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RejectedRecord:
    ingestion_id : int
    source_pk: str | None
    errors: list[dict[str, Any]]