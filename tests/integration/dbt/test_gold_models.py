
from datetime import UTC, datetime
from decimal import Decimal

from conftest import PROJECT_ROOT
from helpers import run_dbt
from psycopg.types.json import Jsonb

BRONZE_SEED_FILE = PROJECT_ROOT / "tests" / "fixtures" / "seed_bronze.sql"


def _seed_bronze(conn):
    with conn.cursor() as cur:
        cur.execute(BRONZE_SEED_FILE.read_text(), prepare=False)
    conn.commit()


def _build_silver(dbt_profile):
    run_dbt(
        dbt_profile,
        "run",
        "--full-refresh",
        "--select",
        "customers",
        "products",
        "orders",
        "order_items",
        "shipments",
    )
    run_dbt(dbt_profile, "snapshot")


def _build_gold(dbt_profile):
    run_dbt(
        dbt_profile,
        "run",
        "--select",
        "path:models/gold",
    )


def test_gold_dimensions_and_facts(
    postgres_warehouse_conn,
    dbt_profile,
):
    _seed_bronze(postgres_warehouse_conn)
    _build_silver(dbt_profile)
    _build_gold(dbt_profile)

    # Product dimension: latest Silver values and unknown member.
    products = postgres_warehouse_conn.execute(
        """
        SELECT product_id, product_name, price
        FROM gold.dim_product
        ORDER BY product_id
        """
    ).fetchall()

    assert products == [
        (-1, "unknown", Decimal("0.00")),
        (201, "Keyboard", Decimal("49.95")),
        (202, "Mouse", Decimal("19.50")),
    ]

    # Customer dimension: current customer versions and unknown member.
    customers = postgres_warehouse_conn.execute(
        """
        SELECT customer_id, last_name, is_current
        FROM gold.dim_customer
        ORDER BY customer_id
        """
    ).fetchall()

    assert customers == [
        (-1, "unknown", True),
        (101, "Lovelace", True),
        (102, "Torvalds", True),
    ]

    # Date dimension: integer date keys and calendar attributes.
    dates = postgres_warehouse_conn.execute(
        """
        SELECT full_date, date_sk, day_of_week, is_weekend
        FROM gold.dim_date
        WHERE full_date IN ('2026-01-01', '2026-01-03')
        ORDER BY full_date
        """
    ).fetchall()

    assert dates == [
        (datetime(2026, 1, 1).date(), 20260101, 4, False),
        (datetime(2026, 1, 3).date(), 20260103, 6, True),
    ]

    # One fact row per order; shipment dates resolve through dim_date.
    orders = postgres_warehouse_conn.execute(
        """
        SELECT
            order_id,
            status,
            order_date_sk,
            carrier,
            shipped_at_sk,
            delivered_at_sk
        FROM gold.fct_orders
        ORDER BY order_id
        """
    ).fetchall()

    assert orders == [
        (1001, "shipped", 20260101, "Carrier A", 20260102, 20260103),
        (1002, "processing", 20260102, "Carrier B", None, None),
    ]

    order_count, distinct_order_count = postgres_warehouse_conn.execute(
        """
        SELECT count(*), count(DISTINCT order_id)
        FROM gold.fct_orders
        """
    ).fetchone()

    assert order_count == distinct_order_count == 2

    # One fact row per order item, with the expected product and measures.
    order_items = postgres_warehouse_conn.execute(
        """
        SELECT
            f.order_item_id,
            f.quantity,
            f.unit_price,
            p.product_id,
            f.order_date_sk
        FROM gold.fct_order_items AS f
        JOIN gold.dim_product AS p
            ON f.product_sk = p.product_sk
        ORDER BY f.order_item_id
        """
    ).fetchall()

    assert order_items == [
        (501, 2, Decimal("49.95"), 201, 20260101),
        (502, 1, Decimal("19.50"), 202, 20260102),
    ]

    item_count, distinct_item_count = postgres_warehouse_conn.execute(
        """
        SELECT count(*), count(DISTINCT order_item_id)
        FROM gold.fct_order_items
        """
    ).fetchone()

    assert item_count == distinct_item_count == 2


def test_fact_order_uses_customer_version_valid_at_order_time(
    postgres_warehouse_conn,
    dbt_profile,
):
    _seed_bronze(postgres_warehouse_conn)

    initial_updated_at = datetime(2026, 2, 1, 12, tzinfo=UTC)
    changed_updated_at = datetime(2026, 2, 3, 12, tzinfo=UTC)

    initial_customer = {
        "id": 301,
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": "Silva",
        "country": "Portugal",
        "city": "Porto",
        "is_active": True,
        "signup_date": "2025-12-01",
        "created_at": initial_updated_at.isoformat(),
        "updated_at": initial_updated_at.isoformat(),
    }

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO bronze.customers (payload) VALUES (%s)",
            (Jsonb(initial_customer),),
        )
    postgres_warehouse_conn.commit()

    # Capture the first customer version in the snapshot.
    _build_silver(dbt_profile)

    changed_customer = {
        **initial_customer,
        "last_name": "Pereira",
        "updated_at": changed_updated_at.isoformat(),
    }

    order = {
        "id": 1099,
        "customer_id": 301,
        "status": "processing",
        "payment_method": "credit_card",
        "order_date": "2026-02-02T12:00:00Z",
        "created_at": "2026-02-02T12:00:00Z",
        "updated_at": "2026-02-02T12:00:00Z",
    }

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO bronze.customers (payload) VALUES (%s)",
            (Jsonb(changed_customer),),
        )
        cur.execute(
            "INSERT INTO bronze.orders (payload) VALUES (%s)",
            (Jsonb(order),),
        )
    postgres_warehouse_conn.commit()

    # Refresh the current customer view and process the new order.
    run_dbt(
        dbt_profile,
        "run",
        "--select",
        "customers",
        "orders",
    )
    run_dbt(dbt_profile, "snapshot")
    _build_gold(dbt_profile)

    # The order was placed between the two customer versions.
    matched_customer = postgres_warehouse_conn.execute(
        """
        SELECT d.last_name, d.is_current
        FROM gold.fct_orders AS f
        JOIN gold.dim_customer AS d
            ON f.customer_sk = d.customer_sk
        WHERE f.order_id = 1099
        """
    ).fetchone()

    assert matched_customer == ("Silva", False)
