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