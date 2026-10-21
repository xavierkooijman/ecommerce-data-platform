import logging
import uuid
from datetime import UTC, datetime
from typing import Literal

from ecommerce_data_platform.storage.base import PipelineRunsStore
from ecommerce_data_platform.types import ExecutionContext, PipelineRun

logger = logging.getLogger(__name__)


class PipelineRunTracker:
    def __init__(
        self,
        stage: str,
        store: PipelineRunsStore,
        source_table: str | None = None,
        execution_context: ExecutionContext | None = None,
    ) -> None:

        self.run = PipelineRun(
            execution_context=execution_context or ExecutionContext(
                run_id=str(uuid.uuid4()),
                task_id=stage,
            ),
            stage=stage,
            source_table=source_table,
        )

        self.store = store

    def __enter__(self) -> PipelineRun:
        self.run.started_at = datetime.now(UTC)

        logger.info(
            f"pipeline stage {self.run.stage} started",
            extra=self._extra_log_fields()
        )

        self.store.start(self.run)

        return self.run

    def __exit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        self.run.finished_at = datetime.now(UTC)

        failed = exc_value is not None

        self.run.status = "failed" if failed else "success"
        self.run.error_message = str(exc_value) if failed else None

        logger.log(
            logging.ERROR if failed else logging.INFO,
            f"pipeline stage {self.run.stage} finished",
            extra=self._extra_log_fields()
        )

        try:
            self.store.finish(self.run)
        except Exception:
            logger.exception(
                f"Failed to persist final pipeline stage {self.run.stage} metrics",
                extra=self._extra_log_fields(),
            )

        return False

    def _extra_log_fields(self) -> dict[str, object]:
        return {
            "run_id": self.run.execution_context.run_id,
            "dag_id": self.run.execution_context.dag_id,
            "task_id": self.run.execution_context.task_id,
            "try_number": self.run.execution_context.try_number,
            "stage": self.run.stage,
            "source_table": self.run.source_table,
            "rows_extracted": self.run.rows_extracted,
            "rows_loaded": self.run.rows_loaded,
            "rows_inspected": self.run.rows_inspected,
            "rows_rejected": self.run.rows_rejected,
        }