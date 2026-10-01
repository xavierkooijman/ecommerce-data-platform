from datetime import date, datetime
from decimal import Decimal


def json_default(obj: object) -> str:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return str(obj)

    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )