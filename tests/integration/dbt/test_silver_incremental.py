from decimal import Decimal

from conftest import PROJECT_ROOT
from helpers import run_dbt


def test_silver_incremental_processing_and_update_precedence(
    postgres_warehouse_conn,
    dbt_profile,
):
    conn = postgres_warehouse_conn

    # Seed the initial Bronze state used to build Silver.
    baseline_seed = (
        PROJECT_ROOT / "tests" / "fixtures" / "seed_incremental_baseline.sql"
    )
    with conn.cursor() as cur:
        cur.execute(baseline_seed.read_text(), prepare=False)
    conn.commit()

    models = ["products", "orders", "order_items", "shipments"]

    # Build the initial Silver state
    run_dbt(
        dbt_profile,
        "run",
        "--full-refresh",
        "--select",
        *models,
    )

    # Seed bronze with second batch
    batch_seed = (
        PROJECT_ROOT / "tests" / "fixtures" / "seed_incremental_batch.sql"
    )
    with conn.cursor() as cur:
        cur.execute(batch_seed.read_text(), prepare=False)
    conn.commit()

    # Run the second batch incrementally
    run_dbt(
        dbt_profile,
        "run",
        "--select",
        *models,
    )

    # Products:
    # 201: newer update replaces the existing product.
    # 202: stale update is ignored; the original Mouse record remains.
    # 204: equal updated_at with a higher ingestion ID replaces the baseline.
    # 205: new product is inserted.
    products = conn.execute(
        """
        SELECT id, product_name, price
        FROM silver.products
        ORDER BY id
        """
    ).fetchall()

    assert products == [
        (201, "Keyboard Updated", Decimal("59.99")),
        (202, "Mouse", Decimal("19.50")),
        (204, "Baseline product Updated", Decimal("31.00")),
        (205, "New product", Decimal("12.50")),
    ]

    # Orders:
    # 1001: newer update changes status to delivered.
    # 1002: stale cancellation is ignored; status remains processing.
    # 1004: equal timestamp with a higher ingestion ID changes status.
    # 1005: new order is inserted.
    orders = conn.execute(
        """
        SELECT id, status
        FROM silver.orders
        WHERE id IN (1001, 1002, 1004, 1005)
        ORDER BY id
        """
    ).fetchall()

    assert orders == [
        (1001, "delivered"),
        (1002, "processing"),
        (1004, "shipped"),
        (1005, "processing"),
    ]

    # Order items:
    # 501: newer update changes quantity and unit price.
    # 502: stale update is ignored; original quantity and price remain.
    # 504: equal timestamp with a higher ingestion ID changes the item.
    # 505: new order item is inserted.
    order_items = conn.execute(
        """
        SELECT id, quantity, unit_price
        FROM silver.order_items
        WHERE id IN (501, 502, 504, 505)
        ORDER BY id
        """
    ).fetchall()

    assert order_items == [
        (501, 3, Decimal("59.99")),
        (502, 1, Decimal("19.50")),
        (504, 2, Decimal("31.00")),
        (505, 4, Decimal("12.50")),
    ]

    # Shipments:
    # 701: newer update changes the carrier/delivery state.
    # 702: stale update is ignored; the original carrier remains.
    # 704: equal timestamp with a higher ingestion ID changes the carrier.
    # 705: new shipment is inserted.
    shipments = conn.execute(
        """
        SELECT id, carrier
        FROM silver.shipments
        WHERE id IN (701, 702, 704, 705)
        ORDER BY id
        """
    ).fetchall()

    assert shipments == [
        (701, "Carrier A"),
        (702, "Carrier B"),
        (704, "Updated Baseline Carrier"),
        (705, "New Carrier"),
    ]