from datetime import date, datetime


def json_default(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )