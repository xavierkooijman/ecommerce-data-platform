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
        watermark = self._checkpoint_store.get(table)

        records = self._extractor.extract(
            table,
            watermark
        )

        if not records:
            return

        try:
            self._landing_store.persist(table, records)
            new_watermark = max(record["updated_at"] for record in records)
            self._checkpoint_store.set(table, new_watermark)
            self._warehouse_conn.commit()
        except Exception:
            self._warehouse_conn.rollback()
            raise

