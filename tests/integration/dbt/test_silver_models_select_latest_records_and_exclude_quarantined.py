from datetime import date
from decimal import Decimal

from conftest import PROJECT_ROOT
from helpers import run_dbt


def test_silver_models_select_latest_records_and_exclude_quarantined(
    postgres_warehouse_conn,
    dbt_profile,
):
    BRONZE_SEED_FILE = PROJECT_ROOT / "tests" / "fixtures" / "seed_bronze.sql"
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(BRONZE_SEED_FILE.read_text(), prepare=False)

    postgres_warehouse_conn.commit()

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

    # Customers: latest version retained; quarantined customer excluded.
    customers = postgres_warehouse_conn.execute(
        """
        SELECT id, email, city, signup_date
        FROM silver.customers
        ORDER BY id
        """
    ).fetchall()

    assert customers == [
        (101, "ada@example.com", "Lisbon", date(2020, 1, 1)),
        (102, "linus@example.com", "Helsinki", date(2021, 5, 12)),
    ]

    # Products: latest price retained; quarantined product excluded.
    products = postgres_warehouse_conn.execute(
        """
        SELECT id, sku, product_name, price
        FROM silver.products
        ORDER BY id
        """
    ).fetchall()

    assert products == [
        (201, "SKU-201", "Keyboard", Decimal("49.95")),
        (202, "SKU-202", "Mouse", Decimal("19.50")),
    ]

    # Orders: latest status retained; quarantined order excluded.
    orders = postgres_warehouse_conn.execute(
        """
        SELECT id, customer_id, status, payment_method
        FROM silver.orders
        ORDER BY id
        """
    ).fetchall()

    assert orders == [
        (1001, 101, "shipped", "credit_card"),
        (1002, 102, "processing", "cash"),
    ]

    # Order items: latest quantity and unit price retained.
    order_items = postgres_warehouse_conn.execute(
        """
        SELECT id, order_id, product_id, quantity, unit_price
        FROM silver.order_items
        ORDER BY id
        """
    ).fetchall()

    assert order_items == [
        (501, 1001, 201, 2, Decimal("49.95")),
        (502, 1002, 202, 1, Decimal("19.50")),
    ]

    # Shipments: latest delivery state retained; null timestamps preserved.
    shipments = postgres_warehouse_conn.execute(
        """
        SELECT id, carrier, delivered_at IS NULL
        FROM silver.shipments
        ORDER BY id
        """
    ).fetchall()

    assert shipments == [
        (701, "Carrier A", False),
        (702, "Carrier B", True),
    ]