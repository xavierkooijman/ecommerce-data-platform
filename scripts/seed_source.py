
import argparse
import os
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import psycopg

REFERENCE_DATE = date(2026, 10, 31)

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

PRICE_RANGES = {
    "Electronics": (15, 800),
    "Clothing": (10, 120),
    "Home": (10, 300),
    "Sports": (10, 200),
    "Books": (5, 40),
    "Beauty": (5, 100),
    "Toys": (5, 150),
    "Accessories": (5, 150),
}

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


# CLI configuration

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and append synthetic e-commerce data."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42).",
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=2000,
        help="Number of new customers (default: 2000).",
    )

    parser.add_argument(
        "--products",
        type=int,
        default=300,
        help="Number of new products (default: 300).",
    )

    parser.add_argument(
        "--orders",
        type=int,
        default=12000,
        help="Number of new orders (default: 12000).",
    )

    args = parser.parse_args()

    if min(args.customers, args.products, args.orders) < 1:
        parser.error("All record counts must be greater than zero.")

    return args


# Helpers

def random_datetime(
    rng: random.Random,
    start: datetime,
    end: datetime,
) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, seconds))


def next_unique_value(
    prefix: str,
    existing_values: set[str],
    suffix: str = "@example.com",
    width: int = 0,
) -> str:
    number = 1

    while True:
        identifier = f"{prefix}{number:0{width}d}{suffix}"

        if identifier not in existing_values:
            existing_values.add(identifier)
            return identifier

        number += 1


# Generate customers

def generate_customers(
    rng: random.Random,
    count: int,
    existing_emails: set[str],
) -> list[tuple]:
    customers = []

    start_date = date(2021, 1, 1)
    latest_signup = REFERENCE_DATE - timedelta(days=14)

    for _ in range(count):
        email = next_unique_value(
            "customer",
            existing_emails,
        )

        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        country = rng.choice(list(COUNTRIES))
        city = rng.choice(COUNTRIES[country])

        signup_date = start_date + timedelta(
            days=rng.randint(0, (latest_signup - start_date).days)
        )

        created_at = datetime.combine(
            signup_date,
            time.min,
            tzinfo=UTC,
        )

        customers.append((
            email,
            first_name,
            last_name,
            country,
            city,
            rng.random() >= 0.05,
            signup_date,
            created_at,
        ))

    return customers


# Generate products

def generate_products(
    rng: random.Random,
    count: int,
    existing_skus: set[str],
) -> list[tuple]:
    products = []

    for _ in range(count):
        sku = next_unique_value(
            "SKU-",
            existing_skus,
            suffix="",
            width=6,
        )

        category = rng.choice(list(PRODUCT_NAMES))
        name = rng.choice(PRODUCT_NAMES[category])

        min_price, max_price = PRICE_RANGES[category]

        price = Decimal(
            str(round(rng.uniform(min_price, max_price), 2))
        )

        created_at = random_datetime(
            rng,
            datetime(2021, 1, 1, tzinfo=UTC),
            datetime.combine(
                REFERENCE_DATE,
                time.min,
                tzinfo=UTC,
            ),
        )

        products.append((
            sku,
            name,
            category,
            price,
            created_at,
        ))

    return products


# Insert data

def main():
    args = parse_args()
    rng = random.Random(args.seed)

    with psycopg.connect(
        host=os.getenv("SOURCE_DB_HOST", "localhost"),
        port=os.getenv("SOURCE_DB_PORT", "5432"),
        user="source_user",
        password=os.environ["SOURCE_DB_PASSWORD"],
        dbname="source",
    ) as conn:
        with conn.cursor() as cur:

            # Retrieve existing unique identifiers.

            cur.execute("SELECT email FROM customers")
            existing_emails = {
                row[0] for row in cur.fetchall()
            }

            cur.execute("SELECT sku FROM products")
            existing_skus = {
                row[0] for row in cur.fetchall()
            }

            # Generate new customers and products.

            customers = generate_customers(
                rng,
                args.customers,
                existing_emails,
            )

            products = generate_products(
                rng,
                args.products,
                existing_skus,
            )

            # Insert customers and retrieve generated IDs.

            customer_records = []

            for customer in customers:
                cur.execute(
                    """
                    INSERT INTO customers (
                        email, first_name, last_name, country, city,
                        is_active, signup_date, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    customer,
                )

                customer_id = cur.fetchone()[0]

                customer_records.append((
                    customer_id,
                    customer[6],  # signup_date
                ))

            # Insert products and retrieve generated IDs.

            product_by_id = {}

            for product in products:
                cur.execute(
                    """
                    INSERT INTO products (
                        sku, name, category, price,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    product,
                )

                product_id = cur.fetchone()[0]

                product_by_id[product_id] = product

            product_ids = list(product_by_id)

            # Generate orders, order items and shipments.

            orders_count = 0
            order_items_count = 0
            shipments_count = 0

            order_start = datetime(2021, 1, 1, tzinfo=UTC)

            order_end = datetime.combine(
                REFERENCE_DATE - timedelta(days=14),
                time.max,
                tzinfo=UTC,
            )

            for _ in range(args.orders):
                customer_id, signup_date = rng.choice(
                    customer_records
                )

                earliest_order = datetime.combine(
                    signup_date,
                    time.min,
                    tzinfo=UTC,
                )

                order_date = random_datetime(
                    rng,
                    max(order_start, earliest_order),
                    order_end,
                )

                status = rng.choices(
                    ORDER_STATUSES,
                    weights=STATUS_WEIGHTS,
                    k=1,
                )[0]

                # Insert order.

                cur.execute(
                    """
                    INSERT INTO orders (
                        customer_id, status, payment_method,
                        order_date, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        customer_id,
                        status,
                        rng.choice(PAYMENT_METHODS),
                        order_date,
                        order_date,
                    ),
                )

                order_id = cur.fetchone()[0]
                orders_count += 1

                # Generate order items.

                items = []

                for _ in range(rng.randint(1, 5)):
                    product_id = rng.choice(product_ids)
                    product = product_by_id[product_id]

                    items.append((
                        order_id,
                        product_id,
                        rng.randint(1, 5),
                        product[3],  # price
                        order_date,
                    ))

                cur.executemany(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, quantity, unit_price,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    items,
                )

                order_items_count += len(items)

                # Generate shipments.

                if status in ("shipped", "delivered", "returned"):
                    shipped_at = order_date + timedelta(
                        hours=rng.randint(2, 72)
                    )

                    delivered_at = None

                    if status in ("delivered", "returned"):
                        delivered_at = shipped_at + timedelta(
                            days=rng.randint(1, 7)
                        )

                    cur.execute(
                        """
                        INSERT INTO shipments (
                            order_id, carrier, shipped_at, delivered_at,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            order_id,
                            rng.choice(CARRIERS),
                            shipped_at,
                            delivered_at,
                            shipped_at,
                        ),
                    )

                    shipments_count += 1

    # Connection context commits the transaction on successful exit.

    print("Data generated and inserted successfully.")
    print(f"Seed:        {args.seed}")
    print(f"Customers:   +{len(customers):,}")
    print(f"Products:    +{len(products):,}")
    print(f"Orders:      +{orders_count:,}")
    print(f"Order items: +{order_items_count:,}")
    print(f"Shipments:   +{shipments_count:,}")


if __name__ == "__main__":
    main()