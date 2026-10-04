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
        checkpoint = self._checkpoint_store.get("validation", table)

        if checkpoint is not None and not isinstance(checkpoint, int):
            raise TypeError(
                "Bronze validation checkpoint must be an integer"
            )

        last_id = checkpoint

        records = self._reader.read(table, last_id)
        if not records:
            return
        rejected = validate(model, records)
        try:
            self._quarantine_store.persist(table, rejected)
            new_checkpoint = max(record.ingestion_id for record in records)
            self._checkpoint_store.set("validation", table, new_checkpoint)
            self._warehouse_conn.commit()
        except Exception:
            self._warehouse_conn.rollback()
            raise

