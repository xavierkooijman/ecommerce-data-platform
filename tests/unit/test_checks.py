from unittest.mock import Mock

from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate_percentage,
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