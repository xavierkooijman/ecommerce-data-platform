INSERT INTO bronze.customers (payload)
VALUES
(
    '{
        "id": 101,
        "email": "old@example.com",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "country": "Portugal",
        "city": "Porto",
        "is_active": true,
        "signup_date": "2020-01-01",
        "created_at": "2026-01-01T09:00:00Z",
        "updated_at": "2026-01-01T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 101,
        "email": "ada@example.com",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "country": "Portugal",
        "city": "Lisbon",
        "is_active": true,
        "signup_date": "2020-01-01",
        "created_at": "2026-01-01T09:00:00Z",
        "updated_at": "2026-01-02T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 102,
        "email": "linus@example.com",
        "first_name": "Linus",
        "last_name": "Torvalds",
        "country": "Finland",
        "city": "Helsinki",
        "is_active": true,
        "signup_date": "2021-05-12",
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-01T10:00:00Z"
    }'::jsonb
);

WITH inserted AS (
    INSERT INTO bronze.customers (payload)
    VALUES (
        '{
            "id": 103,
            "email": "quarantined@example.com",
            "first_name": "Grace",
            "last_name": "Hopper",
            "country": "USA",
            "city": "New York",
            "is_active": true,
            "signup_date": "2022-02-02",
            "created_at": "2026-01-01T11:00:00Z",
            "updated_at": "2026-01-01T11:00:00Z"
        }'::jsonb
    )
    RETURNING ingestion_id
)
INSERT INTO meta.quarantine (source_system, resource, bronze_table, ingestion_id, resource_pk, errors)
SELECT
    'bronze',
    'customers',
    'customers',
    ingestion_id,
    '103',
    '{"errors": ["test quarantine"]}'::jsonb
FROM inserted;


INSERT INTO bronze.products (payload)
VALUES
(
    '{
        "id": 201,
        "sku": "SKU-201",
        "name": "Keyboard",
        "category": "Accessories",
        "price": "39.99",
        "created_at": "2026-01-01T09:00:00Z",
        "updated_at": "2026-01-01T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 201,
        "sku": "SKU-201",
        "name": "Keyboard",
        "category": "Accessories",
        "price": "49.95",
        "created_at": "2026-01-01T09:00:00Z",
        "updated_at": "2026-01-02T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 202,
        "sku": "SKU-202",
        "name": "Mouse",
        "category": "Accessories",
        "price": "19.50",
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-01T10:00:00Z"
    }'::jsonb
);

WITH inserted AS (
    INSERT INTO bronze.products (payload)
    VALUES (
        '{
            "id": 203,
            "sku": "SKU-203",
            "name": "Quarantined product",
            "category": "Accessories",
            "price": "9.99",
            "created_at": "2026-01-01T11:00:00Z",
            "updated_at": "2026-01-01T11:00:00Z"
        }'::jsonb
    )
    RETURNING ingestion_id
)
INSERT INTO meta.quarantine (source_system, resource, bronze_table, ingestion_id, resource_pk, errors)
SELECT
    'bronze',
    'products',
    'products',
    ingestion_id,
    '203',
    '{"errors": ["test quarantine"]}'::jsonb
FROM inserted;

INSERT INTO bronze.orders (payload)
VALUES
(
    '{
        "id": 1001,
        "customer_id": 101,
        "status": "processing",
        "payment_method": "credit_card",
        "order_date": "2026-01-01T12:00:00Z",
        "created_at": "2026-01-01T12:00:00Z",
        "updated_at": "2026-01-01T12:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 1001,
        "customer_id": 101,
        "status": "shipped",
        "payment_method": "credit_card",
        "order_date": "2026-01-01T12:00:00Z",
        "created_at": "2026-01-01T12:00:00Z",
        "updated_at": "2026-01-02T12:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 1002,
        "customer_id": 102,
        "status": "processing",
        "payment_method": "cash",
        "order_date": "2026-01-02T12:00:00Z",
        "created_at": "2026-01-02T12:00:00Z",
        "updated_at": "2026-01-02T12:00:00Z"
    }'::jsonb
);

WITH inserted AS (
    INSERT INTO bronze.orders (payload)
    VALUES (
        '{
            "id": 1003,
            "customer_id": 102,
            "status": "processing",
            "payment_method": "cash",
            "order_date": "2026-01-03T12:00:00Z",
            "created_at": "2026-01-03T12:00:00Z",
            "updated_at": "2026-01-03T12:00:00Z"
        }'::jsonb
    )
    RETURNING ingestion_id
)
INSERT INTO meta.quarantine (source_system, resource, bronze_table, ingestion_id, resource_pk, errors)
SELECT
    'bronze',
    'orders',
    'orders',
    ingestion_id,
    '1003',
    '{"errors": ["test quarantine"]}'::jsonb
FROM inserted;

INSERT INTO bronze.order_items (payload)
VALUES
(
    '{
        "id": 501,
        "order_id": 1001,
        "product_id": 201,
        "quantity": 1,
        "unit_price": "39.99",
        "created_at": "2026-01-01T12:05:00Z",
        "updated_at": "2026-01-01T12:05:00Z"
    }'::jsonb
),
(
    '{
        "id": 501,
        "order_id": 1001,
        "product_id": 201,
        "quantity": 2,
        "unit_price": "49.95",
        "created_at": "2026-01-01T12:05:00Z",
        "updated_at": "2026-01-02T12:05:00Z"
    }'::jsonb
),
(
    '{
        "id": 502,
        "order_id": 1002,
        "product_id": 202,
        "quantity": 1,
        "unit_price": "19.50",
        "created_at": "2026-01-02T12:05:00Z",
        "updated_at": "2026-01-02T12:05:00Z"
    }'::jsonb
);

WITH inserted AS (
    INSERT INTO bronze.order_items (payload)
    VALUES (
        '{
            "id": 503,
            "order_id": 1002,
            "product_id": 202,
            "quantity": 1,
            "unit_price": "19.50",
            "created_at": "2026-01-03T12:05:00Z",
            "updated_at": "2026-01-03T12:05:00Z"
        }'::jsonb
    )
    RETURNING ingestion_id
)
INSERT INTO meta.quarantine (source_system, resource, bronze_table, ingestion_id, resource_pk, errors)
SELECT
    'bronze',
    'order_items',
    'order_items',
    ingestion_id,
    '503',
    '{"errors": ["test quarantine"]}'::jsonb
FROM inserted;

INSERT INTO bronze.shipments (payload)
VALUES
(
    '{
        "id": 701,
        "order_id": 1001,
        "carrier": "Carrier A",
        "shipped_at": "2026-01-02T09:00:00Z",
        "delivered_at": null,
        "created_at": "2026-01-02T09:00:00Z",
        "updated_at": "2026-01-02T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 701,
        "order_id": 1001,
        "carrier": "Carrier A",
        "shipped_at": "2026-01-02T09:00:00Z",
        "delivered_at": "2026-01-03T12:00:00Z",
        "created_at": "2026-01-02T09:00:00Z",
        "updated_at": "2026-01-03T12:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 702,
        "order_id": 1002,
        "carrier": "Carrier B",
        "shipped_at": null,
        "delivered_at": null,
        "created_at": "2026-01-03T09:00:00Z",
        "updated_at": "2026-01-03T09:00:00Z"
    }'::jsonb
);

WITH inserted AS (
    INSERT INTO bronze.shipments (payload)
    VALUES (
        '{
            "id": 703,
            "order_id": 1002,
            "carrier": "Carrier C",
            "shipped_at": "2026-01-03T10:00:00Z",
            "delivered_at": null,
            "created_at": "2026-01-03T10:00:00Z",
            "updated_at": "2026-01-03T10:00:00Z"
        }'::jsonb
    )
    RETURNING ingestion_id
)
INSERT INTO meta.quarantine (source_system, resource, bronze_table, ingestion_id, resource_pk, errors)
SELECT
    'bronze',
    'shipments',
    'shipments',
    ingestion_id,
    '703',
    '{"errors": ["test quarantine"]}'::jsonb
FROM inserted;
