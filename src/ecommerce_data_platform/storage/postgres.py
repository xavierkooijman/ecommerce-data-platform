import json
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from ecommerce_data_platform.records import BronzeRecord, RejectedRecord
from ecommerce_data_platform.types import (
    Checkpoint,
    PipelineRun,
    PipelineStage,
    QuarantineStatus,
)
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

class PostgresBronzeReader:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def read(self, table: str, last_ingestion_id: int | None) -> list[BronzeRecord]:
        query = sql.SQL(
            "SELECT ingestion_id, payload FROM {} WHERE ingestion_id > %s"
        ).format(sql.Identifier("bronze", table))

        with self._conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(query, (last_ingestion_id or 0,))
            return [
                BronzeRecord(
                    ingestion_id=row["ingestion_id"], payload=row["payload"]
                )
                for row in cur.fetchall()
            ]

class PostgresCheckpointStore:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def get(self,
            stage: PipelineStage,
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
        stage: PipelineStage,
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

class PostgresQuarantineStore:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def persist(self, table: str, records: list[RejectedRecord]) -> None:

        with self._conn.cursor() as cur:
            query = """
                INSERT INTO meta.quarantine (source_table, ingestion_id, source_pk, errors)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_table, ingestion_id) DO NOTHING
            """
            values = [
                (
                    table,
                    record.ingestion_id,
                    record.source_pk,
                    Jsonb(record.errors),
                )
                for record in records
            ]

            cur.executemany(query, values)

    def resolve(self, quarantine_id: int, status: QuarantineStatus) -> None:

        with self._conn.cursor() as cur:
            query = """
                UPDATE meta.quarantine
                SET status = %s, resolved_at = NOW()
                WHERE quarantine_id = %s
            """
            cur.execute(query, (status, quarantine_id))

class PostgresPipelineRunsStore:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def start(self, run: PipelineRun) -> None:
        with self._conn.cursor() as cur:
            query = """
                INSERT INTO meta.pipeline_runs (
                    run_id,
                    task_id,
                    dag_id,
                    try_number,
                    stage,
                    source_table,
                    status,
                    started_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(
                query,
                (
                    run.execution_context.run_id,
                    run.execution_context.task_id,
                    run.execution_context.dag_id,
                    run.execution_context.try_number,
                    run.stage,
                    run.source_table,
                    run.status,
                    run.started_at,
                ),
            )

    def finish(self, run: PipelineRun) -> None:
        with self._conn.cursor() as cur:
            query = """
                UPDATE meta.pipeline_runs
                SET status = %s,
                    finished_at = %s,
                    rows_extracted = %s,
                    rows_loaded = %s,
                    rows_inspected = %s,
                    rows_rejected = %s,
                    watermark = %s,
                    error_message = %s
                WHERE run_id = %s AND task_id = %s AND try_number = %s
            """
            cur.execute(
                query,
                (
                    run.status,
                    run.finished_at,
                    run.rows_extracted,
                    run.rows_loaded,
                    run.rows_inspected,
                    run.rows_rejected,
                    run.watermark,
                    run.error_message,
                    run.execution_context.run_id,
                    run.execution_context.task_id,
                    run.execution_context.try_number,
                ),
            )

    def get_consecutive_zero_row_runs(self, source_table: str) -> int:
        with self._conn.cursor() as cur:
            query = """
                WITH recent_runs AS (
                    SELECT
                        ROW_NUMBER() OVER(
                            ORDER BY finished_at DESC
                        ) AS rn,
                        rows_extracted
                    FROM meta.pipeline_runs
                    WHERE
                        status = 'success'
                        AND source_table = %s
                        AND stage = %s
                )

                SELECT COUNT(*)
                FROM recent_runs
                WHERE rows_extracted = 0
                    AND rn < (
                        SELECT COALESCE(
                            MIN(rn) FILTER (WHERE rows_extracted > 0), 
                            COUNT(*)
                        )
                        FROM recent_runs
                )
            """

            cur.execute(query, (source_table, PipelineStage.INGESTION))
            row = cur.fetchone()
            return row[0] if row else 0

    def get_rows_inspected_and_rejected_from_latest_run(self, source_table: str) -> tuple[int, int]:
        with self._conn.cursor() as cur:
            query = """
                SELECT 
                    rows_inspected,
                    rows_rejected
                FROM meta.pipeline_runs
                WHERE status = 'success' AND source_table = %s AND stage = %s
                ORDER BY finished_at DESC
                LIMIT 1
            """
            cur.execute(query, (source_table, PipelineStage.VALIDATION))
            return cur.fetchone() or (0, 0)
        
        
        