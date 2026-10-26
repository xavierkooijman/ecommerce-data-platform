from ecommerce_data_platform.models import DataSource
from ecommerce_data_platform.observability.models import TriggeredCheck
from ecommerce_data_platform.storage.base import PipelineRunStore, QuarantineStore


def check_consecutive_zero_row_runs(
    store: PipelineRunStore, data_source: DataSource, threshold: int
) -> TriggeredCheck | None:
    consecutive_zero_row_runs = store.get_consecutive_zero_row_runs(
        data_source=data_source
    )
    if consecutive_zero_row_runs >= threshold:
        return TriggeredCheck(
            name="consecutive_zero_row_runs",
            observed_value=consecutive_zero_row_runs,
            threshold=threshold,
            data_source=data_source
        )
    return None

def check_rejection_rate_percentage(
    store: PipelineRunStore, data_source: DataSource, threshold: float
) -> TriggeredCheck | None:
    rows_inspected, rows_rejected = (
        store.get_rows_inspected_and_rejected_from_latest_run(
        data_source=data_source
        )
    )
    if rows_inspected == 0:
        return None

    rejection_rate = rows_rejected / rows_inspected * 100
    
    if rejection_rate >= threshold:
        return TriggeredCheck(
            name="rejection_rate_percentage",
            observed_value=rejection_rate,
            threshold=threshold,
            data_source=data_source
        )
    return None

def check_open_quarantine_count(store: QuarantineStore, threshold: int) -> TriggeredCheck | None:

    open_quarantine_count = store.get_open_quarantine_count()

    if open_quarantine_count >= threshold:
        return TriggeredCheck(
            name="open_quarantine_count",
            observed_value=open_quarantine_count,
            threshold=threshold
        )

    return None

def check_oldest_open_quarantine_age_hours(store: QuarantineStore, threshold: float):

    oldest_quarantine_age_hours = store.get_oldest_open_quarantine_age_hours()

    if oldest_quarantine_age_hours >= threshold:
        return TriggeredCheck(
            name="oldest_open_quarantune_age_hours",
            observed_value=oldest_quarantine_age_hours,
            threshold=threshold
        )

    return None

def check_stuck_runs(store: PipelineRunStore, threshold: int) -> TriggeredCheck | None:

    stuck_runs_count = store.get_stuck_runs_count(max_age_minutes=threshold)

    if stuck_runs_count > 0:
        return TriggeredCheck(
            name="stuck_runs",
            observed_value=stuck_runs_count,
            threshold=threshold
        )

    return None

