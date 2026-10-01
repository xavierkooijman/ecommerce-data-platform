from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from ecommerce_data_platform.utils.json import json_default


def test_json_default_serializes_date():
    assert json_default(date(2025, 1, 10)) == "2025-01-10"


def test_json_default_serializes_datetime():
    dt = datetime(2025, 1, 10, 12, 30, tzinfo=UTC)
    assert json_default(dt) == dt.isoformat()


def test_json_default_serializes_decimal():
    assert json_default(Decimal("1299.99")) == "1299.99"

def test_json_default_raises_for_unsupported_type():
    with pytest.raises(TypeError):
        json_default(object())