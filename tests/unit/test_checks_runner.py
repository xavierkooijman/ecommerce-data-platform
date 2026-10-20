from unittest.mock import Mock

import pytest

from ecommerce_data_platform.observability import checks_runner
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    TriggeredCheck,
)


def test_run_checks_completes_when_no_checks_trigger(monkeypatch):
    check = Mock(return_value=None)
    monkeypatch.setattr(
        checks_runner,
        "CHECK_CONFIG",
        {"customers": [Mock(check=check, threshold=3)]},
    )
    monkeypatch.setattr(
        checks_runner,
        "PostgresPipelineRunsStore",
        Mock,
    )

    checks_runner.run_checks("customers")

    check.assert_called_once()


def test_run_checks_raises_when_a_check_triggers(monkeypatch):
    alert = TriggeredCheck(
        name="consecutive_zero_row_runs",
        source_table="customers",
        observed_value=3,
        threshold=3,
    )
    check = Mock(return_value=alert)

    monkeypatch.setattr(
        checks_runner,
        "CHECK_CONFIG",
        {"customers": [Mock(check=check, threshold=3)]},
    )
    monkeypatch.setattr(
        checks_runner,
        "PostgresPipelineRunsStore",
        Mock,
    )

    with pytest.raises(CheckThresholdExceeded):
        checks_runner.run_checks("customers")

    check.assert_called_once()