from ecommerce_data_platform.storage.postgres import PostgresLandingStore

def test_persist_customers(postgres_warehouse_conn):
    records = [
        {"id": 1, "email": "alice@example.com"},
        {"id": 2, "email": "bob@example.com"},
    ]

    store = PostgresLandingStore(postgres_warehouse_conn)

    inserted = store.persist("customers", records)

    assert inserted == 2

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute("""
            SELECT payload
            FROM bronze.customers
            ORDER BY ingestion_id
        """)

        payloads = [row[0] for row in cur.fetchall()]

    assert payloads == records

def test_persist_empty_records(postgres_warehouse_conn):
    store = PostgresLandingStore(postgres_warehouse_conn)

    assert store.persist("customers", []) == 0

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bronze.customers")
        assert cur.fetchone()[0] == 0