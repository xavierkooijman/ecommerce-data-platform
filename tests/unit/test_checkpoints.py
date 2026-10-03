from datetime import UTC, datetime

import pytest

from ecommerce_data_platform.utils.checkpoints import checkpoint_to_columns, columns_to_checkpoint


def test_checkpoint_to_columns_returns_timestamp_checkpoint():
    checkpoint = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    checkpoint_ts, checkpoint_num = checkpoint_to_columns(
        checkpoint
    )

    assert checkpoint_ts == checkpoint
    assert checkpoint_num is None

def test_checkpoint_to_columns_returns_int_checkpoint():
    checkpoint = 123

    checkpoint_ts, checkpoint_num = checkpoint_to_columns(
        checkpoint
    )

    assert checkpoint_ts is None
    assert checkpoint_num == 123

def test_checkpoint_to_columns_rejects_string():
    with pytest.raises(
        TypeError,
        match="Unsupported checkpoint type: str",
    ):
        checkpoint_to_columns("abc")

def test_checkpoint_to_columns_rejects_bool():
    with pytest.raises(
        TypeError,
        match="Unsupported checkpoint type: bool",
    ):
        checkpoint_to_columns(True)

def test_columns_to_checkpoint_returns_timestamp():
    checkpoint = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    result = columns_to_checkpoint(
        checkpoint_ts=checkpoint,
        checkpoint_num=None,
    )

    assert result == checkpoint

def test_columns_to_checkpoint_returns_int():
    result = columns_to_checkpoint(
        checkpoint_ts=None,
        checkpoint_num=123,
    )

    assert result == 123

def test_columns_to_checkpoint_raises_when_both_values_are_none():
    with pytest.raises(
        ValueError,
        match="Checkpoint row contains no checkpoint value",
    ):
        columns_to_checkpoint(
            checkpoint_ts=None,
            checkpoint_num=None,
        )

def test_columns_to_checkpoint_raises_when_both_values_are_set():
    checkpoint = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    with pytest.raises(ValueError):
        columns_to_checkpoint(
            checkpoint_ts=checkpoint,
            checkpoint_num=123,
        )