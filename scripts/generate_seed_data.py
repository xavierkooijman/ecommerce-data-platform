
import os
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import psycopg

# Configuration

SEED = 42

NUM_CUSTOMERS = 2000
NUM_PRODUCTS = 300
NUM_ORDERS = 12000

REFERENCE_DATE = date(2026, 10, 31)

rng = random.Random(SEED)


# Reference data

COUNTRIES = {
    "Portugal": ["Porto", "Lisbon", "Braga", "Coimbra", "Faro"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville"],
    "France": ["Paris", "Lyon", "Marseille", "Bordeaux"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne"],
    "United Kingdom": ["London", "Manchester", "Liverpool"],
    "Italy": ["Rome", "Milan", "Naples", "Florence"],
    "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht"],
    "United States": ["New York", "Los Angeles", "Chicago", "Boston"],
}

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William",
    "David", "Daniel", "Thomas", "Oliver", "Lucas",
    "Emma", "Olivia", "Sophia", "Isabella", "Mia",
    "Charlotte", "Amelia", "Emily", "Ava", "Lily",
]

LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Taylor", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin",
    "Garcia", "Martinez", "Robinson", "Clark", "Lewis",
]

PRODUCT_NAMES = {
    "Electronics": ["Headphones", "Keyboard", "Mouse", "Monitor", "Speaker"],
    "Clothing": ["T-Shirt", "Hoodie", "Jeans", "Jacket", "Sneakers"],
    "Home": ["Lamp", "Chair", "Desk", "Pillow", "Blanket"],
    "Sports": ["Yoga Mat", "Dumbbells", "Water Bottle", "Backpack"],
    "Books": ["Novel", "Cookbook", "Biography", "Notebook"],
    "Beauty": ["Face Cream", "Shampoo", "Perfume", "Sunscreen"],
    "Toys": ["Puzzle", "Board Game", "Building Blocks", "Action Figure"],
    "Accessories": ["Wallet", "Watch", "Sunglasses", "Belt"],
}

CATEGORIES = list(PRODUCT_NAMES)

PAYMENT_METHODS = [
    "credit_card",
    "paypal",
    "apple_pay",
    "bank_transfer",
    "google_pay",
]

ORDER_STATUSES = [
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    "returned",
]

STATUS_WEIGHTS = [15, 15, 50, 10, 10]

CARRIERS = ["DHL", "UPS", "FedEx", "DPD", "GLS"]


# Helpers

def random_datetime(start: datetime, end: datetime) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, seconds))


# Generate customers

customers = []

start_date = date(2021, 1, 1)
latest_signup = REFERENCE_DATE - timedelta(days=14)

for customer_id in range(1, NUM_CUSTOMERS + 1):
    first_name = rng.choice(FIRST_NAMES)
    last_name = rng.choice(LAST_NAMES)

    country = rng.choice(list(COUNTRIES))
    city = rng.choice(COUNTRIES[country])

    signup_date = start_date + timedelta(
        days=rng.randint(0, (latest_signup - start_date).days)
    )

    created_at = datetime.combine(
        signup_date, time.min, tzinfo=UTC
    )

    customers.append((
        customer_id,
        f"customer{customer_id}@example.com",
        first_name,
        last_name,
        country,
        city,
        rng.random() >= 0.05,
        signup_date,
        created_at,
        created_at,
    ))


# Generate products

products = []

for product_id in range(1, NUM_PRODUCTS + 1):
    category = rng.choice(CATEGORIES)
    name = rng.choice(PRODUCT_NAMES[category])

    price = Decimal(str(round(rng.uniform(5, 1500), 2)))

    created_at = random_datetime(
        datetime(2021, 1, 1, tzinfo=UTC),
        datetime.combine(REFERENCE_DATE, time.min, tzinfo=UTC),
    )

    products.append((
        product_id,
        f"SKU-{product_id:06d}",
        name,
        category,
        price,
        created_at,
        created_at,
    ))


# Generate orders, order items and shipments

orders = []
order_items = []
shipments = []

product_by_id = {product[0]: product for product in products}

order_start = datetime(2021, 1, 1, tzinfo=UTC)
order_end = datetime.combine(
    REFERENCE_DATE - timedelta(days=14),
    time.max,
    tzinfo=UTC,
)

for order_id in range(1, NUM_ORDERS + 1):
    customer = rng.choice(customers)

    customer_id = customer[0]
    signup_date = customer[7]

    earliest_order = datetime.combine(
        signup_date, time.min, tzinfo=UTC
    )

    order_date = random_datetime(
        max(order_start, earliest_order),
        order_end,
    )

    status = rng.choices(
        ORDER_STATUSES,
        weights=STATUS_WEIGHTS,
        k=1,
    )[0]

    orders.append((
        order_id,
        customer_id,
        status,
        rng.choice(PAYMENT_METHODS),
        order_date,
        order_date,
        order_date,
    ))

    # Generate 1-5 items per order.

    for _ in range(rng.randint(1, 5)):
        product_id = rng.randint(1, NUM_PRODUCTS)
        product = product_by_id[product_id]

        order_items.append((
            len(order_items) + 1,
            order_id,
            product_id,
            rng.randint(1, 5),
            product[4],
            order_date,
            order_date,
        ))

    # Generate shipments for shipped, delivered and returned orders.

    if status in ("shipped", "delivered", "returned"):
        shipped_at = order_date + timedelta(
            hours=rng.randint(2, 72)
        )

        delivered_at = None

        if status in ("delivered", "returned"):
            delivered_at = shipped_at + timedelta(
                days=rng.randint(1, 7)
            )

        shipments.append((
            len(shipments) + 1,
            order_id,
            rng.choice(CARRIERS),
            shipped_at,
            delivered_at,
            shipped_at,
            shipped_at,
        ))


# Insert data

with psycopg.connect(
    host=os.getenv("SOURCE_DB_HOST", "localhost"),
    port=os.getenv("SOURCE_DB_PORT", "5432"),
    user="source_user",
    password=os.environ["SOURCE_DB_PASSWORD"],
    dbname="source",
) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO customers (
                id, email, first_name, last_name, country, city,
                is_active, signup_date, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            customers,
        )

        cur.executemany(
            """
            INSERT INTO products (
                id, sku, name, category, price, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            products,
        )

        cur.executemany(
            """
            INSERT INTO orders (
                id, customer_id, status, payment_method,
                order_date, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            orders,
        )

        cur.executemany(
            """
            INSERT INTO order_items (
                id, order_id, product_id, quantity, unit_price,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            order_items,
        )

        cur.executemany(
            """
            INSERT INTO shipments (
                id, order_id, carrier, shipped_at, delivered_at,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            shipments,
        )

        # Synchronize SERIAL sequences with inserted IDs.

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
                    (SELECT MAX(id) FROM {table})
                )
                """
            )


print("Data generated and inserted successfully.")
print(f"Customers:   {len(customers):,}")
print(f"Products:    {len(products):,}")
print(f"Orders:      {len(orders):,}")
print(f"Order items: {len(order_items):,}")
print(f"Shipments:   {len(shipments):,}")
