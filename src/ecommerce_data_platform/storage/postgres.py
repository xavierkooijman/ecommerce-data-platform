import json
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from ecommerce_data_platform.types import Checkpoint
from ecommerce_data_platform.utils.checkpoints import checkpoint_to_columns, columns_to_checkpoint
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

    def get(self,
            stage: str,
            source_table: str
            ) -> Checkpoint | None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT checkpoint_ts, checkpoint_num 
                FROM meta.checkpoints 
                WHERE stage = %s AND source_table = %s
                """,
                (stage, source_table),
            )

            row = cur.fetchone()

        if row is None:
            return None

        checkpoint_ts, checkpoint_num = row

        return columns_to_checkpoint(checkpoint_ts, checkpoint_num)

    def set(
        self,
        stage: str,
        source_table: str,
        checkpoint: Checkpoint,
    ) -> None:
        
        checkpoint_ts, checkpoint_num = checkpoint_to_columns(checkpoint)

        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO meta.checkpoints (
                    stage,
                    source_table,
                    checkpoint_ts,
                    checkpoint_num
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (stage, source_table)
                DO UPDATE SET
                    checkpoint_ts = EXCLUDED.checkpoint_ts,
                    checkpoint_num = EXCLUDED.checkpoint_num,
                    updated_at = NOW()
                """,
                (
                    stage,
                    source_table,
                    checkpoint_ts,
                    checkpoint_num,
                ),
            )

        
        
        