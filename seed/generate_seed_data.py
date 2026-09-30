"""
Seed data generator for the source (OLTP) PostgreSQL database.

The generator produces valid operational data rather than deliberately
invalid records. The interesting scenarios come from normal application
behaviour:

- Customers can be updated after creation.
- Products can have their current price changed over time.
- Orders progress through realistic lifecycle states.
- Shipments are created after their corresponding orders.
- Delivery happens after shipment.
- Different tables have different update patterns.
- Order volume contains seasonal peaks.
- Nullable fields represent genuinely optional source attributes.

The generated data is deterministic when SEED is fixed.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import psycopg

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42

N_CUSTOMERS = 2_000
N_PRODUCTS = 300
N_ORDERS = 12_000

YEARS_BACK = 5

CUSTOMER_UPDATE_RATE = 0.25
PRODUCT_UPDATE_RATE = 0.30

INACTIVE_CUSTOMER_RATE = 0.05

COUNTRIES_CITIES: dict[str, list[str]] = {
    "Portugal": ["Lisbon", "Porto", "Braga", "Coimbra", "Faro"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse"],
    "USA": ["New York", "Chicago", "Austin", "Seattle"],
    "UK": ["London", "Manchester", "Bristol", "Leeds"],
}

FIRST_NAMES = [
    "Maria",
    "Joao",
    "Ana",
    "Pedro",
    "Sofia",
    "Miguel",
    "Ines",
    "Tiago",
    "Carla",
    "Bruno",
    "Rita",
    "Nuno",
    "Catarina",
    "Diogo",
    "Beatriz",
]

LAST_NAMES = [
    "Silva",
    "Santos",
    "Ferreira",
    "Pereira",
    "Costa",
    "Rodrigues",
    "Martins",
    "Oliveira",
    "Sousa",
    "Carvalho",
]

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Books",
    "Sports",
    "Home",
    "Beauty",
    "Toys",
    "Food",
]

PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Electronics": (20, 1500),
    "Clothing": (10, 200),
    "Books": (5, 60),
    "Sports": (10, 400),
    "Home": (5, 800),
    "Beauty": (5, 150),
    "Toys": (5, 120),
    "Food": (2, 50),
}

PAYMENT_METHODS = [
    "credit_card",
    "paypal",
    "apple_pay",
    "bank_transfer",
    "google_pay",
]

CARRIERS = [
    "DHL",
    "FedEx",
    "UPS",
    "CTT Express",
    "GLS",
]

rng = random.Random(SEED)
NOW = datetime.now(UTC)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_signup_date() -> date:
    days_back = rng.randint(0, YEARS_BACK * 365)
    return (NOW - timedelta(days=days_back)).date()


def random_country_city() -> tuple[str, str]:
    country = rng.choice(list(COUNTRIES_CITIES))
    city = rng.choice(COUNTRIES_CITIES[country])
    return country, city


def seasonal_order_date() -> datetime:
    """
    Generate an order date across the last five years.

    Order volume is deliberately concentrated around common retail
    periods while retaining normal background demand.
    """
    year_offset = rng.randint(0, YEARS_BACK - 1)
    year = NOW.year - year_offset

    bucket = rng.random()

    if bucket < 0.25:
        # Black Friday period
        base = datetime(year, 11, 24, tzinfo=UTC)
        day_jitter = rng.randint(-2, 4)

    elif bucket < 0.45:
        # Christmas period
        base = datetime(year, 12, 18, tzinfo=UTC)
        day_jitter = rng.randint(-3, 7)

    elif bucket < 0.60:
        # Summer sales
        base = datetime(year, 7, 10, tzinfo=UTC)
        day_jitter = rng.randint(-5, 10)

    else:
        # Normal demand
        base = datetime(year, 1, 1, tzinfo=UTC)
        day_jitter = rng.randint(0, 364)

    dt = base + timedelta(
        days=day_jitter,
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )

    if dt > NOW:
        dt = NOW - timedelta(days=1)

    return dt


def skewed_quantity() -> int:
    """
    Most order items have small quantities, with a smaller long tail.
    """
    r = rng.random()

    if r < 0.60:
        return rng.randint(1, 2)

    if r < 0.90:
        return rng.randint(3, 5)

    return rng.randint(6, 10)


def random_later_timestamp(
    start: datetime,
    min_days: int = 1,
    max_days: int = 30,
) -> datetime:
    """Generate a timestamp after `start`."""
    return start + timedelta(
        days=rng.randint(min_days, max_days),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )


def generate_product_price(category: str) -> Decimal:
    low, high = PRICE_RANGES[category]
    return Decimal(str(round(rng.uniform(low, high), 2)))


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class GeneratedData:
    customers: list[dict] = field(default_factory=list)
    products: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    order_items: list[dict] = field(default_factory=list)
    shipments: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def generate_customers(n: int) -> list[dict]:
    customers = []

    for customer_id in range(1, n + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)

        country, city = random_country_city()

        signup_date = random_signup_date()

        created_at = datetime.combine(
            signup_date,
            datetime.min.time(),
            tzinfo=UTC,
        )

        updated_at = created_at

        # Some customers have subsequently changed profile information.
        if rng.random() < CUSTOMER_UPDATE_RATE:
            updated_at = random_later_timestamp(
                created_at,
                min_days=30,
                max_days=900,
            )

            # A normal customer profile change may include a move.
            if rng.random() < 0.50:
                country, city = random_country_city()

        # A small percentage of customers have no city recorded.
        # This is a legitimate nullable source attribute rather than
        # deliberately corrupted data.
        if rng.random() < 0.10:
            city = None

        customers.append(
            {
                "id": customer_id,
                "email": f"{first.lower()}.{last.lower()}{customer_id}@example.com",
                "first_name": first,
                "last_name": last,
                "country": country,
                "city": city,
                "is_active": rng.random() >= INACTIVE_CUSTOMER_RATE,
                "signup_date": signup_date,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return customers


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def generate_products(n: int) -> list[dict]:
    products = []

    for product_id in range(1, n + 1):
        category = rng.choice(CATEGORIES)
        price = generate_product_price(category)

        created_at = NOW - timedelta(
            days=rng.randint(0, YEARS_BACK * 365)
        )

        updated_at = created_at

        # Products can be updated after creation, for example when their
        # current price changes.
        if rng.random() < PRODUCT_UPDATE_RATE:
            updated_at = random_later_timestamp(
                created_at,
                min_days=30,
                max_days=900,
            )

            price_change = rng.uniform(0.85, 1.15)
            price = max(
                Decimal("0.01"),
                (price * Decimal(str(price_change))).quantize(
                    Decimal("0.01")
                ),
            )

        products.append(
            {
                "id": product_id,
                "sku": f"{category[:3].upper()}-{product_id:05d}",
                "name": f"{category} item {product_id}",
                "category": category,
                "price": price,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return products


# ---------------------------------------------------------------------------
# Orders and order items
# ---------------------------------------------------------------------------

def generate_order_status(order_date: datetime) -> tuple[str, datetime]:
    """
    Generate a plausible current order status and the timestamp of the
    latest status change.

    Older orders are much more likely to have reached a terminal state.
    Recent orders can still be processing or shipped.
    """
    age_days = (NOW - order_date).days

    if age_days <= 2:
        choices = [
            ("processing", 0.55),
            ("shipped", 0.35),
            ("cancelled", 0.10),
        ]

    elif age_days <= 7:
        choices = [
            ("processing", 0.15),
            ("shipped", 0.45),
            ("delivered", 0.30),
            ("cancelled", 0.10),
        ]

    else:
        choices = [
            ("delivered", 0.75),
            ("returned", 0.10),
            ("shipped", 0.05),
            ("cancelled", 0.10),
        ]

    r = rng.random()
    cumulative = 0.0

    for status, probability in choices:
        cumulative += probability

        if r <= cumulative:
            if status == "processing":
                updated_at = order_date + timedelta(
                    hours=rng.randint(1, 24)
                )

            elif status == "shipped":
                updated_at = order_date + timedelta(
                    days=rng.randint(1, 3)
                )

            elif status == "delivered":
                updated_at = order_date + timedelta(
                    days=rng.randint(3, 10)
                )

            elif status == "returned":
                updated_at = order_date + timedelta(
                    days=rng.randint(10, 30)
                )

            else:
                updated_at = order_date + timedelta(
                    hours=rng.randint(1, 72)
                )

            return status, min(updated_at, NOW)

    raise RuntimeError("Unable to generate order status")


def generate_orders_and_items(
    n_orders: int,
    customers: list[dict],
    products: list[dict],
) -> tuple[list[dict], list[dict]]:
    orders = []
    order_items = []

    item_id = 1

    for order_id in range(1, n_orders + 1):
        customer = rng.choice(customers)
        order_date = seasonal_order_date()

        status, updated_at = generate_order_status(order_date)

        orders.append(
            {
                "id": order_id,
                "customer_id": customer["id"],
                "status": status,
                "payment_method": rng.choice(PAYMENT_METHODS),
                "order_date": order_date,
                "created_at": order_date,
                "updated_at": updated_at,
            }
        )

        for _ in range(rng.randint(1, 5)):
            product = rng.choice(products)

            quantity = skewed_quantity()

            order_items.append(
                {
                    "id": item_id,
                    "order_id": order_id,
                    "product_id": product["id"],
                    "quantity": quantity,

                    # Preserve the actual transaction price.
                    # This is intentionally independent from the product's
                    # current price.
                    "unit_price": product["price"],

                    "created_at": order_date,
                    "updated_at": order_date,
                }
            )

            item_id += 1

    return orders, order_items


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------

def generate_shipments(orders: list[dict]) -> list[dict]:
    """
    Generate shipment records for orders that entered the shipping process.

    Shipment rows are created after the original order, modelling a normal
    operational workflow where the shipment record does not exist at the
    time the order is initially created.

    Some deliveries are deliberately delayed, producing late updates to
    shipment records.
    """
    shipments = []
    shipment_id = 1

    for order in orders:
        if order["status"] not in {
            "shipped",
            "delivered",
            "returned",
        }:
            continue

        order_date = order["order_date"]

        ship_delay = timedelta(
            days=rng.randint(1, 3),
            hours=rng.randint(0, 23),
        )

        shipped_at = order_date + ship_delay

        # The shipment record enters the source system around the time
        # the shipment is created.
        created_at = shipped_at

        delivered_at = None

        if order["status"] in {"delivered", "returned"}:
            delivery_delay = timedelta(
                days=rng.randint(2, 7)
            )

            # Some shipments take substantially longer.
            if rng.random() < 0.10:
                delivery_delay += timedelta(
                    days=rng.randint(3, 10)
                )

            delivered_at = shipped_at + delivery_delay

        updated_at = delivered_at or shipped_at

        shipments.append(
            {
                "id": shipment_id,
                "order_id": order["id"],
                "carrier": rng.choice(CARRIERS),
                "shipped_at": shipped_at,
                "delivered_at": delivered_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        shipment_id += 1

    return shipments


# ---------------------------------------------------------------------------
# Generate everything
# ---------------------------------------------------------------------------

def generate_all() -> GeneratedData:
    data = GeneratedData()

    data.customers = generate_customers(N_CUSTOMERS)

    data.products = generate_products(N_PRODUCTS)

    data.orders, data.order_items = generate_orders_and_items(
        N_ORDERS,
        data.customers,
        data.products,
    )

    data.shipments = generate_shipments(data.orders)

    return data


# ---------------------------------------------------------------------------
# PostgreSQL loading
# ---------------------------------------------------------------------------

def copy_load(
    conn: psycopg.Connection,
    table: str,
    columns: list[str],
    rows: list[dict],
) -> None:
    if not rows:
        return

    col_list = ", ".join(columns)

    with conn.cursor() as cur:
        with cur.copy(
            f"COPY {table} ({col_list}) FROM STDIN"
        ) as copy:
            for row in rows:
                copy.write_row(
                    tuple(row[column] for column in columns)
                )


def load_into_postgres(
    conn: psycopg.Connection,
    data: GeneratedData,
) -> None:
    copy_load(
        conn,
        "customers",
        [
            "id",
            "email",
            "first_name",
            "last_name",
            "country",
            "city",
            "is_active",
            "signup_date",
            "created_at",
            "updated_at",
        ],
        data.customers,
    )

    copy_load(
        conn,
        "products",
        [
            "id",
            "sku",
            "name",
            "category",
            "price",
            "created_at",
            "updated_at",
        ],
        data.products,
    )

    copy_load(
        conn,
        "orders",
        [
            "id",
            "customer_id",
            "status",
            "payment_method",
            "order_date",
            "created_at",
            "updated_at",
        ],
        data.orders,
    )

    copy_load(
        conn,
        "order_items",
        [
            "id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "created_at",
            "updated_at",
        ],
        data.order_items,
    )

    copy_load(
        conn,
        "shipments",
        [
            "id",
            "order_id",
            "carrier",
            "shipped_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ],
        data.shipments,
    )


def reset_sequences(conn: psycopg.Connection) -> None:
    """
    COPY inserts explicit SERIAL IDs, so reset the sequences afterwards
    to prevent collisions with future application inserts.
    """
    with conn.cursor() as cur:
        for table in (
            "customers",
            "products",
            "orders",
            "order_items",
            "shipments",
        ):
            cur.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1)
                )
                """
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dsn = os.environ.get(
        "SOURCE_DB_DSN",
        "postgresql://postgres:postgres@localhost:5432/source_db",
    )

    data = generate_all()

    print(
        f"Generated: "
        f"{len(data.customers)} customers, "
        f"{len(data.products)} products, "
        f"{len(data.orders)} orders, "
        f"{len(data.order_items)} order_items, "
        f"{len(data.shipments)} shipments"
    )

    with psycopg.connect(dsn) as conn:
        load_into_postgres(conn, data)
        reset_sequences(conn)
        conn.commit()

    print("Done.")