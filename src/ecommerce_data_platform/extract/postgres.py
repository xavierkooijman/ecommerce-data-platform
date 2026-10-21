from datetime import datetime
from typing import Any

import psycopg
from psycopg import sql

from ecommerce_data_platform.utils.db import source_connection


class PostgresIncrementalExtractor:

    def extract(
        self,
        table: str,
        watermark: datetime | None,
        watermark_column: str = "updated_at",
    ) -> list[dict[str, Any]]:
        with source_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                if watermark is None:
                    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                    cur.execute(query)
                else:
                    query = sql.SQL(
                        "SELECT * FROM {} WHERE {} > %(watermark)s"
                    ).format(
                        sql.Identifier(table),
                        sql.Identifier(watermark_column),
                    )
                    cur.execute(query, {"watermark": watermark})
                return cur.fetchall()