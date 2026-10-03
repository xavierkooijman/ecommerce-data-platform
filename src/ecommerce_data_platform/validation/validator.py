from pydantic import BaseModel, ValidationError

from ecommerce_data_platform.records import RejectedRecord
from ecommerce_data_platform.storage.base import BronzeRecord


def validate(
    model: type[BaseModel], records: list[BronzeRecord]
) -> list[RejectedRecord]:
    rejected: list[RejectedRecord] = []
    for record in records:
        try:
            model.model_validate(record.payload)
        except ValidationError as exc:
            rejected.append(RejectedRecord(
                record.ingestion_id,
                str(record.payload.get("id")) if "id" in record.payload else None,
                errors = [
                    dict(error)
                    for error in exc.errors(
                        include_url=False, include_context=False, include_input=False
                    )
                ],
            ))
    return rejected