INSERT INTO bronze.products (payload)
VALUES
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
        "updated_at": "2026-01-02T10:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 204,
        "sku": "SKU-204",
        "name": "Baseline product",
        "category": "Accessories",
        "price": "30.00",
        "created_at": "2026-01-04T09:00:00Z",
        "updated_at": "2026-01-04T09:00:00Z"
    }'::jsonb
);

INSERT INTO bronze.orders (payload)
VALUES
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
),
(
    '{
        "id": 1004,
        "customer_id": 101,
        "status": "processing",
        "payment_method": "cash",
        "order_date": "2026-01-04T09:00:00Z",
        "created_at": "2026-01-04T09:00:00Z",
        "updated_at": "2026-01-04T09:00:00Z"
    }'::jsonb
);

INSERT INTO bronze.order_items (payload)
VALUES
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
),
(
    '{
        "id": 504,
        "order_id": 1004,
        "product_id": 204,
        "quantity": 1,
        "unit_price": "30.00",
        "created_at": "2026-01-04T09:05:00Z",
        "updated_at": "2026-01-04T09:05:00Z"
    }'::jsonb
);

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
        "id": 702,
        "order_id": 1002,
        "carrier": "Carrier B",
        "shipped_at": "2026-01-02T09:00:00Z",
        "delivered_at": null,
        "created_at": "2026-01-02T09:00:00Z",
        "updated_at": "2026-01-02T09:00:00Z"
    }'::jsonb
),
(
    '{
        "id": 704,
        "order_id": 1004,
        "carrier": "Baseline Carrier",
        "shipped_at": "2026-01-04T10:00:00Z",
        "delivered_at": null,
        "created_at": "2026-01-04T10:00:00Z",
        "updated_at": "2026-01-04T10:00:00Z"
    }'::jsonb
);