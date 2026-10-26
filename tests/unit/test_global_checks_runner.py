from unittest.mock import Mock

import pytest

from ecommerce_data_platform.observability import global_checks_runner
from ecommerce_data_platform.observability.models import (
    CheckThresholdExceeded,
    TriggeredCheck,
)


def test_run_global_checks_completes_when_no_checks_trigger():
    check = Mock(return_value=None)

    global_checks_runner.run_global_checks([check])

    check.assert_called_once_with()

def test_run_global_checks_raises_when_a_check_triggers():
    alert = TriggeredCheck(
        name="open_quarantine_count",
        data_source=None,
        observed_value=150,
        threshold=100,
    )
    check = Mock(return_value=alert)

    with pytest.raises(CheckThresholdExceeded):
        global_checks_runner.run_global_checks([check])

    check.assert_called_once_with()