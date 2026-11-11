
import os
from datetime import UTC, datetime

import psycopg
from psycopg.types.json import Jsonb


def generate_invalid_records() -> dict[str, dict]:
    now = datetime.now(UTC).isoformat()
    base_id = int(datetime.now(UTC).timestamp() * 1_000_000)

    return {
        "customers": {
            "id": base_id,
            "email": "not-an-email",
            "first_name": "John",
            "last_name": "Doe",
            "country": "Portugal",
            "city": "Porto",
            "is_active": True,
            "signup_date": "2026-10-01",
            "created_at": now,
            "updated_at": now,
        },
        "products": {
            "id": base_id + 1,
            "sku": f"INVALID-{base_id}",
            "name": "Invalid Product",
            "category": "Electronics",
            "price": -10.99,
            "created_at": now,
            "updated_at": now,
        },
        "orders": {
            "id": base_id + 2,
            "customer_id": 1,
            "status": "unknown_status",
            "payment_method": "credit_card",
            "order_date": now,
            "created_at": now,
            "updated_at": now,
        },
        "order_items": {
            "id": base_id + 3,
            "order_id": 1,
            "product_id": 1,
            "quantity": -5,
            "unit_price": 19.99,
            "created_at": now,
            "updated_at": now,
        },
        "shipments": {
            "id": base_id + 4,
            "order_id": 1,
            "carrier": "DHL",
            "shipped_at": "not-a-valid-datetime",
            "delivered_at": None,
            "created_at": now,
            "updated_at": now,
        },
    }


def main() -> None:
    records = generate_invalid_records()

    conn = psycopg.connect(
        host=os.getenv("WAREHOUSE_DB_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_DB_PORT", "5433")),
        user="warehouse_user",
        password=os.environ["WAREHOUSE_DB_PASSWORD"],
        dbname="warehouse",
    )

    with conn:
        with conn.cursor() as cur:
            for table, payload in records.items():
                cur.execute(
                    f"""
                    INSERT INTO bronze.{table} (payload)
                    VALUES (%s)
                    """,
                    (Jsonb(payload),),
                )

                print(f"Inserted invalid record into bronze.{table}")

    conn.close()
    print("Finished injecting invalid records.")


if __name__ == "__main__":
    main()
