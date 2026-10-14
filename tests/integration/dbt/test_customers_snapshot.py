from datetime import UTC, datetime

from helpers import run_dbt
from psycopg.types.json import Jsonb


def test_customer_snapshot_history(
    postgres_warehouse_conn,
    dbt_profile,
):
    conn = postgres_warehouse_conn

    initial_updated_at = datetime(2026, 1, 2, 12, tzinfo=UTC)
    changed_updated_at = datetime(2026, 1, 3, 12, tzinfo=UTC)

    customer = {
        "id": 301,
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": "Silva",
        "country": "Portugal",
        "city": "Porto",
        "is_active": True,
        "signup_date": "2025-12-01",
        "created_at": "2025-12-01T10:00:00Z",
        "updated_at": initial_updated_at.isoformat(),
    }

    # Insert the initial customer version into Bronze.
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.customers (payload)
            VALUES (%s)
            """,
            (Jsonb(customer),),
        )
    conn.commit()

    # Capture the initial version in the snapshot.
    run_dbt(dbt_profile, "run", "--select", "customers")
    run_dbt(dbt_profile, "snapshot")

    initial_version = conn.execute(
        """
        SELECT last_name, dbt_valid_from, dbt_valid_to
        FROM silver.customers_snapshot
        WHERE customer_id = 301
        """
    ).fetchone()

    assert initial_version == ("Silva", initial_updated_at, None)

    # Insert a newer version of the same customer.
    customer["last_name"] = "Pereira"
    customer["updated_at"] = changed_updated_at.isoformat()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.customers (payload)
            VALUES (%s)
            """,
            (Jsonb(customer),),
        )
    conn.commit()

    # Capture the change in a second snapshot run.
    run_dbt(dbt_profile, "run", "--select", "customers")
    run_dbt(dbt_profile, "snapshot")

    history = conn.execute(
        """
        SELECT last_name, dbt_valid_from, dbt_valid_to
        FROM silver.customers_snapshot
        WHERE customer_id = 301
        ORDER BY dbt_valid_from
        """
    ).fetchall()

    assert history == [
        ("Silva", initial_updated_at, changed_updated_at),
        ("Pereira", changed_updated_at, None),
    ]

