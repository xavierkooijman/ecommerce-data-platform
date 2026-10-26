from unittest.mock import Mock

from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate_percentage,
    check_open_quarantine_count,
    check_oldest_open_quarantine_age_hours,
    check_stuck_runs
)
from ecommerce_data_platform.observability.models import TriggeredCheck


def test_zero_row_check_triggers_at_threshold(data_source):
    store = Mock()
    store.get_consecutive_zero_row_runs.return_value = 3

    result = check_consecutive_zero_row_runs(store, data_source, 3)

    assert isinstance(result, TriggeredCheck)
    assert result.name == "consecutive_zero_row_runs"
    assert result.data_source == data_source
    assert result.observed_value == 3
    assert result.threshold == 3


def test_zero_row_check_does_not_trigger_below_threshold(data_source):
    store = Mock()
    store.get_consecutive_zero_row_runs.return_value = 2

    result = check_consecutive_zero_row_runs(store, data_source, 3)

    assert result is None


def test_rejection_rate_triggers_at_threshold(data_source):
    store = Mock()
    store.get_rows_inspected_and_rejected_from_latest_run.return_value = (
        100,
        10,
    )

    result = check_rejection_rate_percentage(store, data_source, 10.0)

    assert isinstance(result, TriggeredCheck)
    assert result.name == "rejection_rate_percentage"
    assert result.data_source == data_source
    assert result.observed_value == 10.0
    assert result.threshold == 10.0



def test_rejection_rate_does_not_trigger_below_threshold(data_source):
    store = Mock()
    store.get_rows_inspected_and_rejected_from_latest_run.return_value = (
        100,
        9,
    )

    result = check_rejection_rate_percentage(store, data_source, 10.0)

    assert result is None


def test_rejection_rate_skips_when_no_rows_inspected(data_source):
    store = Mock()
    store.get_rows_inspected_and_rejected_from_latest_run.return_value = (
        0,
        0,
    )

    result = check_rejection_rate_percentage(store, data_source, 10.0)

    assert result is None

def test_open_quarantine_count_triggers_at_threshold():
    store = Mock()
    store.get_open_quarantine_count.return_value = 100

    result = check_open_quarantine_count(store, 100)

    assert isinstance(result, TriggeredCheck)
    assert result.name == "open_quarantine_count"
    assert result.observed_value == 100
    assert result.threshold == 100

def test_open_quarantine_count_does_not_trigger_below_threshold():
    store = Mock()
    store.get_open_quarantine_count.return_value = 99

    result = check_open_quarantine_count(store, 100)

    assert result is None

def test_oldest_open_quarantine_age_hours_triggers_at_threshold():
    store = Mock()
    store.get_oldest_open_quarantine_age_hours.return_value = 48.0

    result = check_oldest_open_quarantine_age_hours(store, 48.0)

    assert isinstance(result, TriggeredCheck)
    assert result.name == "oldest_open_quarantune_age_hours"
    assert result.observed_value == 48.0
    assert result.threshold == 48.0

def test_oldest_open_quarantine_age_hours_does_not_trigger_below_threshold():
    store = Mock()
    store.get_oldest_open_quarantine_age_hours.return_value = 47.0

    result = check_oldest_open_quarantine_age_hours(store, 48.0)

    assert result is None

def test_stuck_runs_triggers_when_stuck_runs_exist():
    store = Mock()
    store.get_stuck_runs_count.return_value = 5

    result = check_stuck_runs(store, 15)

    assert isinstance(result, TriggeredCheck)
    assert result.name == "stuck_runs"
    assert result.observed_value == 5
    assert result.threshold == 15

def test_stuck_runs_does_not_trigger_when_no_stuck_runs():
    store = Mock()
    store.get_stuck_runs_count.return_value = 0

    result = check_stuck_runs(store, 15)

    assert result is None