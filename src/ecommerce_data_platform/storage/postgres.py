import json
from typing import Any

from psycopg import sql
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from ecommerce_data_platform.models import (
    BronzeRecord,
    BronzeTable,
    Checkpoint,
    DataSource,
    PipelineRun,
    PipelineStage,
    PostgresConnectionFactory,
    QuarantineStatus,
    RejectedRecord,
)
from ecommerce_data_platform.utils.checkpoints import checkpoint_to_columns, columns_to_checkpoint
from ecommerce_data_platform.utils.json import json_default


class PostgresBronzeStore:
    def __init__(self, connection_factory: PostgresConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def persist(self, table: BronzeTable, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0

        query = sql.SQL("COPY {} (payload) FROM STDIN").format(sql.Identifier("bronze", table))

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
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

    def read(self, table: BronzeTable, last_ingestion_id: int | None) -> list[BronzeRecord]:
        query = sql.SQL(
            "SELECT ingestion_id, payload FROM {} WHERE ingestion_id > %s"
        ).format(sql.Identifier("bronze", table))
        with self._connection_factory() as conn:
            with self._connection_factory() as conn:
                with conn.cursor(row_factory=class_row(BronzeRecord)) as cur:
                    cur.execute(query, (last_ingestion_id or 0,))
                    return cur.fetchall()

class PostgresCheckpointStore:
    def __init__(self, connection_factory: PostgresConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def get(
        self,
        stage: PipelineStage,
        data_source: DataSource
    ) -> Checkpoint | None:
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                """
                SELECT checkpoint_ts, checkpoint_num 
                FROM meta.checkpoints 
                WHERE stage = %s AND source_system = %s AND resource = %s
                """,
                (stage, data_source.source_system, data_source.resource),
            )

            row = cur.fetchone()

        if row is None:
            return None

        checkpoint_ts, checkpoint_num = row

        return columns_to_checkpoint(checkpoint_ts, checkpoint_num)

    def set(
        self,
        stage: PipelineStage,
        data_source: DataSource,
        checkpoint: Checkpoint,
    ) -> None:
        
        checkpoint_ts, checkpoint_num = checkpoint_to_columns(checkpoint)

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                """
                INSERT INTO meta.checkpoints (
                    stage,
                    source_system,
                    resource,
                    checkpoint_ts,
                    checkpoint_num
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (stage, source_system, resource)
                DO UPDATE SET
                    checkpoint_ts = EXCLUDED.checkpoint_ts,
                    checkpoint_num = EXCLUDED.checkpoint_num,
                    updated_at = NOW()
                """,
                (
                    stage,
                    data_source.source_system,
                    data_source.resource,
                    checkpoint_ts,
                    checkpoint_num,
                ),
            )

class PostgresQuarantineStore:
    def __init__(self, connection_factory: PostgresConnectionFactory):
        self._connection_factory = connection_factory

    def persist(
        self, 
        data_source: DataSource, 
        table: BronzeTable, 
        records: list[RejectedRecord]
    ) -> None:

        query = """
                INSERT INTO meta.quarantine (
                    source_system,
                    resource,
                    resource_pk,
                    bronze_table,
                    ingestion_id,
                    errors
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (bronze_table, ingestion_id) DO NOTHING
            """
        values = [
                (
                    data_source.source_system,
                    data_source.resource,
                    record.resource_pk,
                    table,
                    record.ingestion_id,
                    Jsonb(record.errors),
                )
                for record in records
            ]

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, values)

    def resolve(self, quarantine_id: int, status: QuarantineStatus) -> None:

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE meta.quarantine
                    SET status = %s, resolved_at = NOW()
                    WHERE quarantine_id = %s
                """, 
                (status, quarantine_id)
            )

    def get_open_quarantine_count(self) -> int:

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                """
                SELECT COUNT(*)
                FROM meta.quarantine
                WHERE status = 'open'
                """
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def get_oldest_open_quarantine_age_hours(self) -> int | float:

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXTRACT(EPOCH FROM (NOW() - MIN(quarantined_at))) / 3600.0
                    FROM meta.quarantine
                    WHERE status = 'open'
                    """
                )
                row = cur.fetchone()
                return row[0] if row else 0

class PostgresPipelineRunStore:
    def __init__(self, connection_factory: PostgresConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def start(self, run: PipelineRun) -> None:
        query = """
            INSERT INTO meta.pipeline_runs (
                run_id,
                task_id,
                dag_id,
                try_number,
                stage,
                source_system,
                resource,
                status,
                started_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        run.execution_context.run_id,
                        run.execution_context.task_id,
                        run.execution_context.dag_id,
                        run.execution_context.try_number,
                        run.stage,
                        run.data_source.source_system,
                        run.data_source.resource,
                        run.status,
                        run.started_at,
                ),
            )

    def finish(self, run: PipelineRun) -> None:
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
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
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

    def get_consecutive_zero_row_runs(self, data_source: DataSource) -> int:
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
                AND source_system = %s
                AND resource = %s
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
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (data_source.source_system, data_source.resource, PipelineStage.INGESTION),
                )
                row = cur.fetchone()
                return row[0] if row else 0

    def get_rows_inspected_and_rejected_from_latest_run(
        self, 
        data_source: DataSource
    ) -> tuple[int, int]:
        query = """
            SELECT 
                rows_inspected,
                rows_rejected
            FROM meta.pipeline_runs
            WHERE status = 'success' AND source_system = %s AND resource = %s AND stage = %s
            ORDER BY finished_at DESC
            LIMIT 1
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (data_source.source_system, data_source.resource, PipelineStage.VALIDATION),
                )
                return cur.fetchone() or (0, 0)


        