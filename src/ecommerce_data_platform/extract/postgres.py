import psycopg
from psycopg import sql
from typing import Any

class IncrementalPostgresExtractor:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def extract(self, table: str, watermark: str | None, watermark_column: str = "updated_at") -> list[dict[str, Any]]:
        with self._conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            if watermark is None:
                query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                cur.execute(query)
            else:
                query = sql.SQL("SELECT * FROM {} WHERE {} > %(watermark)s").format(sql.Identifier(table), sql.Identifier(watermark_column))
                cur.execute(query, {"watermark": watermark})
            return cur.fetchall()