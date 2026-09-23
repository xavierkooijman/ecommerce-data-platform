"""
Seed data generator for the source (OLTP) Postgres database.

Design notes (read before running):

- Uses only the standard library `random` + a small hand-rolled fake-name/city
  pool, so it has zero extra dependencies. If you already have `Faker`
  installed and want richer names/addresses, swap `random_name()` /
  `random_city()` for Faker calls — the rest of the structure doesn't change.

- Everything is deterministic if you set a fixed SEED, which you want for a
  teaching/testing dataset: reruns produce identical data, so your pipeline
  tests are reproducible.

- Data-quality issues are injected via explicit probability constants at the
  top of the file (DQ_* constants) — tune them, or set to 0.0 to generate a
  "clean" run for comparison.

- Writes directly to Postgres via psycopg, using COPY for speed (same
  technique benchmarked in Topic 12) — 10k+ rows insert in well under a
  second rather than minutes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, UTC

import psycopg

# ---------------------------------------------------------------------------
# Configuration — tune freely
# ---------------------------------------------------------------------------

SEED = 42
N_CUSTOMERS = 2_000
N_PRODUCTS = 300
N_ORDERS = 12_000
YEARS_BACK = 5

# Data-quality injection rates (probabilities, 0.0–1.0)
DQ_MISSING_EMAIL = 0.03
DQ_MISSING_CITY = 0.10
DQ_DUPLICATE_EMAIL_RATE = 0.02   # fraction of customers who reuse another's email
DQ_DUPLICATE_SKU_RATE = 0.02     # fraction of products that reuse another's SKU
DQ_NEGATIVE_QUANTITY = 0.01      # fraction of order_items with a negative qty
DQ_FUTURE_ORDER_DATE = 0.005     # fraction of orders dated in the future
DQ_INVALID_STATUS = 0.01         # fraction of orders with a nonsense status
INACTIVE_CUSTOMER_RATE = 0.05

COUNTRIES_CITIES: dict[str, list[str]] = {
    "Portugal": ["Lisbon", "Porto", "Braga", "Coimbra", "Faro"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse"],
    "USA": ["New York", "Chicago", "Austin", "Seattle"],
    "UK": ["London", "Manchester", "Bristol", "Leeds"],
}

FIRST_NAMES = ["Maria", "Joao", "Ana", "Pedro", "Sofia", "Miguel", "Ines", "Tiago",
               "Carla", "Bruno", "Rita", "Nuno", "Catarina", "Diogo", "Beatriz"]
LAST_NAMES = ["Silva", "Santos", "Ferreira", "Pereira", "Costa", "Rodrigues",
              "Martins", "Oliveira", "Sousa", "Carvalho"]

CATEGORIES = ["Electronics", "Clothing", "Books", "Sports", "Home", "Beauty", "Toys", "Food"]
# realistic-ish price ranges per category: (min, max)
PRICE_RANGES = {
    "Electronics": (20, 1500),
    "Clothing": (10, 200),
    "Books": (5, 60),
    "Sports": (10, 400),
    "Home": (5, 800),
    "Beauty": (5, 150),
    "Toys": (5, 120),
    "Food": (2, 50),
}

STATUSES = ["delivered"] * 70 + ["shipped"] * 15 + ["cancelled"] * 10 + ["returned"] * 5
INVALID_STATUSES = ["proccessing", "UNKNOWN", "", "pending-ish", "n/a"]
PAYMENT_METHODS = ["credit_card", "paypal", "apple_pay", "bank_transfer", "google_pay"]
CARRIERS = ["DHL", "FedEx", "UPS", "CTT Express", "GLS"]

rng = random.Random(SEED)
NOW = datetime.now(UTC)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_signup_date() -> date:
    days_back = rng.randint(0, YEARS_BACK * 365)
    return (NOW - timedelta(days=days_back)).date()


def random_country_city() -> tuple[str, str | None]:
    country = rng.choice(list(COUNTRIES_CITIES.keys()))
    if rng.random() < DQ_MISSING_CITY:
        return country, None
    return country, rng.choice(COUNTRIES_CITIES[country])


def seasonal_order_date() -> datetime:
    """Weighted toward Black Friday, Christmas, and a summer sale window,
    spread across the last YEARS_BACK years."""
    year_offset = rng.randint(0, YEARS_BACK - 1)
    year = NOW.year - year_offset

    bucket = rng.random()
    if bucket < 0.25:
        # Black Friday window (late Nov)
        base = datetime(year, 11, 24, tzinfo=UTC)
        day_jitter = rng.randint(-2, 4)
    elif bucket < 0.45:
        # Christmas window
        base = datetime(year, 12, 18, tzinfo=UTC)
        day_jitter = rng.randint(-3, 7)
    elif bucket < 0.60:
        # Summer sale window
        base = datetime(year, 7, 10, tzinfo=UTC)
        day_jitter = rng.randint(-5, 10)
    else:
        # uniform background demand across the year
        base = datetime(year, 1, 1, tzinfo=UTC)
        day_jitter = rng.randint(0, 364)

    dt = base + timedelta(days=day_jitter, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
    if dt > NOW:
        dt = NOW - timedelta(days=1)  # clamp accidental overshoot into the past
    return dt


def skewed_quantity() -> int:
    """Most orders have small quantities; a long tail has more."""
    r = rng.random()
    if r < 0.6:
        return rng.randint(1, 2)
    elif r < 0.9:
        return rng.randint(3, 5)
    else:
        return rng.randint(6, 10)


# ---------------------------------------------------------------------------
# Entity generation
# ---------------------------------------------------------------------------

@dataclass
class GeneratedData:
    customers: list[dict] = field(default_factory=list)
    products: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    order_items: list[dict] = field(default_factory=list)
    shipments: list[dict] = field(default_factory=list)


def generate_customers(n: int) -> list[dict]:
    customers = []
    used_emails: list[str] = []

    for i in range(1, n + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        country, city = random_country_city()
        signup = random_signup_date()
        created_at = datetime.combine(signup, datetime.min.time(), tzinfo=UTC)

        if rng.random() < DQ_MISSING_EMAIL:
            email = None
        elif used_emails and rng.random() < DQ_DUPLICATE_EMAIL_RATE:
            email = rng.choice(used_emails)  # deliberate duplicate
        else:
            email = f"{first.lower()}.{last.lower()}{i}@example.com"
            used_emails.append(email)

        customers.append({
            "id": i,
            "email": email,
            "first_name": first,
            "last_name": last,
            "country": country,
            "city": city,
            "is_active": rng.random() >= INACTIVE_CUSTOMER_RATE,
            "signup_date": signup,
            "created_at": created_at,
            "updated_at": created_at,
        })
    return customers


def generate_products(n: int) -> list[dict]:
    products = []
    used_skus: list[str] = []

    for i in range(1, n + 1):
        category = rng.choice(CATEGORIES)
        low, high = PRICE_RANGES[category]
        price = round(rng.uniform(low, high), 2)

        if used_skus and rng.random() < DQ_DUPLICATE_SKU_RATE:
            sku = rng.choice(used_skus)
        else:
            sku = f"{category[:3].upper()}-{i:05d}"
            used_skus.append(sku)

        created_at = NOW - timedelta(days=rng.randint(0, YEARS_BACK * 365))
        products.append({
            "id": i,
            "sku": sku,
            "name": f"{category} item {i}",
            "category": category,
            "price": price,
            "created_at": created_at,
            "updated_at": created_at,
        })
    return products


def generate_orders_and_items(n_orders: int, customers: list[dict], products: list[dict]):
    orders = []
    order_items = []
    item_id = 1

    for order_id in range(1, n_orders + 1):
        customer = rng.choice(customers)
        order_date = seasonal_order_date()

        if rng.random() < DQ_FUTURE_ORDER_DATE:
            order_date = NOW + timedelta(days=rng.randint(1, 30))  # deliberate bad data

        status = rng.choice(INVALID_STATUSES) if rng.random() < DQ_INVALID_STATUS else rng.choice(STATUSES)

        orders.append({
            "id": order_id,
            "customer_id": customer["id"],
            "status": status,
            "payment_method": rng.choice(PAYMENT_METHODS),
            "order_date": order_date,
            "created_at": order_date,
            "updated_at": order_date,
        })

        for _ in range(rng.randint(1, 5)):
            product = rng.choice(products)
            qty = skewed_quantity()
            if rng.random() < DQ_NEGATIVE_QUANTITY:
                qty = -qty  # deliberate bad data

            order_items.append({
                "id": item_id,
                "order_id": order_id,
                "product_id": product["id"],
                "quantity": qty,
                "unit_price": product["price"],
                "created_at": order_date,
                "updated_at": order_date,
            })
            item_id += 1

    return orders, order_items


def generate_shipments(orders: list[dict]) -> list[dict]:
    """Only 'shipped'/'delivered'/'returned' orders get a shipment row.
    Models late-arriving data: shipped_at / delivered_at trail order_date
    by a realistic delay, and some are still in transit (delivered_at NULL)."""
    shipments = []
    shipment_id = 1

    for order in orders:
        if order["status"] not in ("shipped", "delivered", "returned"):
            continue

        order_date = order["order_date"]
        ship_delay = timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 23))
        shipped_at = order_date + ship_delay

        delivered_at = None
        if order["status"] in ("delivered", "returned"):
            deliver_delay = timedelta(days=rng.randint(2, 7))
            if rng.random() < 0.1:
                deliver_delay += timedelta(days=rng.randint(3, 10))  # simulate a delayed delivery
            delivered_at = shipped_at + deliver_delay

        shipments.append({
            "id": shipment_id,
            "order_id": order["id"],
            "carrier": rng.choice(CARRIERS),
            "shipped_at": shipped_at,
            "delivered_at": delivered_at,
            "created_at": shipped_at,
            "updated_at": delivered_at or shipped_at,
        })
        shipment_id += 1

    return shipments


def generate_all() -> GeneratedData:
    data = GeneratedData()
    data.customers = generate_customers(N_CUSTOMERS)
    data.products = generate_products(N_PRODUCTS)
    data.orders, data.order_items = generate_orders_and_items(N_ORDERS, data.customers, data.products)
    data.shipments = generate_shipments(data.orders)
    return data


# ---------------------------------------------------------------------------
# Loading into Postgres via COPY
# ---------------------------------------------------------------------------

def copy_load(conn: psycopg.Connection, table: str, columns: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    col_list = ", ".join(columns)
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({col_list}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(tuple(row[c] for c in columns))


def load_into_postgres(conn: psycopg.Connection, data: GeneratedData) -> None:
    copy_load(conn, "customers",
              ["id", "email", "first_name", "last_name", "country", "city",
               "is_active", "signup_date", "created_at", "updated_at"],
              data.customers)

    copy_load(conn, "products",
              ["id", "sku", "name", "category", "price", "created_at", "updated_at"],
              data.products)

    # customers/products must commit (or at least flush) before orders,
    # since orders/order_items/shipments carry real FK references
    copy_load(conn, "orders",
              ["id", "customer_id", "status", "payment_method", "order_date",
               "created_at", "updated_at"],
              data.orders)

    copy_load(conn, "order_items",
              ["id", "order_id", "product_id", "quantity", "unit_price",
               "created_at", "updated_at"],
              data.order_items)

    copy_load(conn, "shipments",
              ["id", "order_id", "carrier", "shipped_at", "delivered_at",
               "created_at", "updated_at"],
              data.shipments)


def reset_sequences(conn: psycopg.Connection) -> None:
    """SERIAL PRIMARY KEYs don't know we inserted explicit IDs via COPY —
    without this, the next real INSERT (e.g. from a test) would collide
    with an ID we already used."""
    with conn.cursor() as cur:
        for table in ("customers", "products", "orders", "order_items", "shipments"):
            cur.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            )


if __name__ == "__main__":
    import os

    dsn = os.environ.get("SOURCE_DB_DSN", "postgresql://postgres:postgres@localhost:5432/source_db")
    data = generate_all()

    print(f"Generated: {len(data.customers)} customers, {len(data.products)} products, "
          f"{len(data.orders)} orders, {len(data.order_items)} order_items, "
          f"{len(data.shipments)} shipments")

    with psycopg.connect(dsn) as conn:
        load_into_postgres(conn, data)
        reset_sequences(conn)
        conn.commit()

    print("Done.")