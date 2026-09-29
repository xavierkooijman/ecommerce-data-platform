import json
from datetime import datetime
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from ecommerce_data_platform.utils.json import json_default


class PostgresLandingStore:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def persist(self, table: str, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0

        query = sql.SQL("COPY {} (payload) FROM STDIN").format(sql.Identifier("bronze", table))
        
        with self._conn.cursor() as cur:
            with cur.copy(query) as copy:
                for record in records:
                    copy.write_row(
                        (
                            Jsonb(
                                record,
                                dumps=lambda obj: json.dumps(obj, default=json_default),
                            ),
                        )
                    )

        return len(records)


class PostgresCheckpointStore:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def get(self, pipeline_name: str) -> datetime | None:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT watermark FROM meta.pipeline_checkpoints WHERE pipeline_name = %s",
                (pipeline_name,),
            )

            row = cur.fetchone()
            return row[0] if row else None

    def set(self, pipeline_name: str, watermark: datetime) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta.pipeline_checkpoints (pipeline_name, watermark) "
                "VALUES (%s, %s) "
                "ON CONFLICT(pipeline_name) DO UPDATE SET "
                "watermark = EXCLUDED.watermark, updated_at = NOW()",
                (pipeline_name, watermark),
            )

        
        
        