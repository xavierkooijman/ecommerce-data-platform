from datetime import UTC, datetime

from ecommerce_data_platform.records import BronzeRecord
from ecommerce_data_platform.validation.models import Customer
from ecommerce_data_platform.validation.validator import validate


def test_validate_returns_no_rejected_records_for_valid_records():
    records = [
        BronzeRecord(
            ingestion_id=1,
            payload={
                "id": 1,
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "country": "PT",
                "city": "Porto",
                "is_active": True,
                "signup_date": "2025-01-01",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
    ]

    rejected = validate(Customer, records)

    assert rejected == []

def test_validate_returns_rejected_record_for_invalid_records():
    records = [
        BronzeRecord(
            ingestion_id=42,
            payload={
                "id": 1,
                "email": "not-an-email",
            },
        )
    ]

    rejected = validate(Customer, records)

    assert len(rejected) == 1

    assert rejected[0].ingestion_id == 42
    assert rejected[0].source_pk == "1"
    assert len(rejected[0].errors) > 0

def test_validate_sets_source_pk_to_none_when_id_missing():
    records = [
        BronzeRecord(
            ingestion_id=42,
            payload={
                "email": "not-an-email",
            },
        )
    ]

    rejected = validate(Customer, records)

    assert len(rejected) == 1
    assert rejected[0].source_pk is None