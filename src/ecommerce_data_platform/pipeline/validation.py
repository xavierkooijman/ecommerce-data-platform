import psycopg
from pydantic import BaseModel

from ecommerce_data_platform.storage.base import BronzeReader, CheckpointStore, QuarantineStore
from ecommerce_data_platform.validation.validator import validate


class BronzeValidationJob:
    def __init__(
        self,
        reader: BronzeReader,
        quarantine_store: QuarantineStore,
        checkpoint_store: CheckpointStore,
        warehouse_conn: psycopg.Connection,
    ):
        self._reader = reader
        self._quarantine_store = quarantine_store
        self._checkpoint_store = checkpoint_store
        self._warehouse_conn = warehouse_conn

    def run(self, table: str, model: type[BaseModel]) -> None:
        last_id = self._checkpoint_store.get(table)
        records = self._reader.read(table, last_id)
        if not records:
            return
        rejected = validate(model, records)
        try:
            self._quarantine_store.persist(table, rejected)
            new_checkpoint = max(record.ingestion_id for record in records)
            self._checkpoint_store.set(table, new_checkpoint)
            self._warehouse_conn.commit()
        except Exception:
            self._warehouse_conn.rollback()
            raise

