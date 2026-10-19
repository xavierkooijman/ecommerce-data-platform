from ecommerce_data_platform.observability.models import TriggeredCheck
from ecommerce_data_platform.storage.base import PipelineRunsStore
from ecommerce_data_platform.types import SourceTable


def check_consecutive_zero_row_runs(
    store: PipelineRunsStore, source_table: SourceTable, threshold: int
) -> TriggeredCheck | None:
    consecutive_zero_row_runs = store.get_consecutive_zero_row_runs(
        source_table=source_table
    )
    if consecutive_zero_row_runs >= threshold:
        return TriggeredCheck(
            name="consecutive_zero_row_runs",
            source_table=source_table,
            observed_value=consecutive_zero_row_runs,
            threshold=threshold,
        )
    return None

def check_rejection_rate(
    store: PipelineRunsStore, source_table: SourceTable, threshold: float
) -> TriggeredCheck | None:
    rows_inspected, rows_rejected = (
        store.get_rows_inspected_and_rejected_from_latest_run(
        source_table=source_table
        )
    )
    if rows_inspected == 0:
        return None

    rejection_rate = rows_rejected / rows_inspected
    
    if rejection_rate >= threshold:
        return TriggeredCheck(
            name="rejection_rate",
            source_table=source_table,
            observed_value=rejection_rate,
            threshold=threshold,
        )
    return None

