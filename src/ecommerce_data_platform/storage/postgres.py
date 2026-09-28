import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from typing import Any

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
                    copy.write_row((Jsonb(record),))

        return len(records)
        
        