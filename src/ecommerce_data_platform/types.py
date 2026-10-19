from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

type Checkpoint = int | datetime

class QuarantineStatus(StrEnum):
    OPEN = "open"
    REVALIDATED = "revalidated"
    SUPERSEDED = "superseded"
    WONT_FIX = "wont_fix"

class PipelineStage(StrEnum):
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"


@dataclass(frozen=True)
class ExecutionContext:
    run_id: str
    task_id: str
    dag_id: str | None = None
    try_number: int = 1


@dataclass
class PipelineRun:
    execution_context: ExecutionContext
    stage: str
    source_table: str | None = None
    status: str = "running"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    rows_extracted: int = 0
    rows_loaded: int = 0
    rows_inspected: int = 0
    rows_rejected: int = 0
    watermark: datetime | None = None
    error_message: str | None = None