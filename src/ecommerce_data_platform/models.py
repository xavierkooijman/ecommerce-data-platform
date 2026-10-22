from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

import psycopg

type Checkpoint = int | datetime

type PostgresConnectionFactory = Callable[[], psycopg.Connection]

class SourceSystem(StrEnum):
    ECOMMERCE_DB = "ecommerce_db"

class Resource(StrEnum):
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    SHIPMENTS = "shipments"

@dataclass(frozen=True)
class DataSource:
    source_system: SourceSystem
    resource: Resource

class SourceTable(StrEnum):
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    SHIPMENTS = "shipments"

class BronzeTable(StrEnum):
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    SHIPMENTS = "shipments"
    

class QuarantineStatus(StrEnum):
    OPEN = "open"
    REVALIDATED = "revalidated"
    SUPERSEDED = "superseded"
    WONT_FIX = "wont_fix"

class PipelineStage(StrEnum):
    INGESTION = "ingestion"
    VALIDATION = "validation"

@dataclass(frozen=True, slots=True)
class BronzeRecord:
    ingestion_id: int
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RejectedRecord:
    ingestion_id : int
    resource_pk: str | None
    errors: list[dict[str, Any]]


@dataclass(frozen=True)
class ExecutionContext:
    run_id: str
    task_id: str
    dag_id: str | None = None
    try_number: int = 1


class PipelineRunStatus(StrEnum):
    RUNNING = "runnig"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class PipelineRun:
    execution_context: ExecutionContext
    stage: str
    data_source: DataSource
    status: PipelineRunStatus = PipelineRunStatus.RUNNING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    rows_extracted: int = 0
    rows_loaded: int = 0
    rows_inspected: int = 0
    rows_rejected: int = 0
    watermark: datetime | None = None
    error_message: str | None = None