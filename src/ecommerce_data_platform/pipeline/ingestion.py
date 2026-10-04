from datetime import datetime

import psycopg

from ecommerce_data_platform.extract.base import IncrementalExtractor
from ecommerce_data_platform.storage.base import CheckpointStore, LandingStore


class EcommerceIncrementalIngestion:
    def __init__(
        self,
        extractor: IncrementalExtractor,
        landing_store: LandingStore,
        checkpoint_store: CheckpointStore,
        warehouse_conn: psycopg.Connection,
    ):
        self._extractor = extractor
        self._landing_store = landing_store
        self._checkpoint_store = checkpoint_store
        self._warehouse_conn = warehouse_conn

    def run(self, table: str) -> None:
        checkpoint = self._checkpoint_store.get("ingestion", table)

        if checkpoint is not None and not isinstance(checkpoint, datetime):
            raise TypeError(
                "Incremental ingestion checkpoint must be a datetime"
            )

        watermark = checkpoint

        records = self._extractor.extract(
            table,
            watermark
        )

        if not records:
            return

        try:
            self._landing_store.persist(table, records)
            new_checkpoint = max(record["updated_at"] for record in records)
            self._checkpoint_store.set("ingestion", table, new_checkpoint)
            self._warehouse_conn.commit()
        except Exception:
            self._warehouse_conn.rollback()
            raise

