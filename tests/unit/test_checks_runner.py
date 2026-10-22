from unittest.mock import Mock

import pytest

from ecommerce_data_platform.observability import checks_runner
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    TriggeredCheck,
)


def test_run_checks_completes_when_no_checks_trigger(monkeypatch, data_source):
    check = Mock(return_value=None)
    store = Mock()

    monkeypatch.setattr(
        checks_runner,
        "CHECK_CONFIG",
        {data_source: [Mock(check=check, threshold=3)]},
    )

    checks_runner.run_checks(data_source, store)

    check.assert_called_once_with(store, data_source, 3)


def test_run_checks_raises_when_a_check_triggers(monkeypatch, data_source):
    alert = TriggeredCheck(
        name="consecutive_zero_row_runs",
        data_source=data_source,
        observed_value=3,
        threshold=3,
    )
    check = Mock(return_value=alert)
    store = Mock()

    monkeypatch.setattr(
        checks_runner,
        "CHECK_CONFIG",
        {data_source: [Mock(check=check, threshold=3)]},
    )

    with pytest.raises(CheckThresholdExceeded):
        checks_runner.run_checks(data_source, store)

    check.assert_called_once_with(store, data_source, 3)