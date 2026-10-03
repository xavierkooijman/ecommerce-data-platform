from datetime import datetime

from ecommerce_data_platform.types import Checkpoint


def checkpoint_to_columns(
    checkpoint: Checkpoint,
) -> tuple[datetime | None, int | None]:
    if isinstance(checkpoint, datetime):
        return checkpoint, None

    if isinstance(checkpoint, int) and not isinstance(checkpoint, bool):
        return None, checkpoint

    raise TypeError(
        f"Unsupported checkpoint type: {type(checkpoint).__name__}"
    )

def columns_to_checkpoint(
    checkpoint_ts: datetime | None,
    checkpoint_num: int | None,
) -> Checkpoint:
    if checkpoint_ts is not None and checkpoint_num is not None:
        raise ValueError(
            "Checkpoint row contains multiple checkpoint values"
        )

    if checkpoint_ts is not None:
        return checkpoint_ts

    if checkpoint_num is not None:
        return checkpoint_num

    raise ValueError(
        "Checkpoint row contains no checkpoint value"
    )