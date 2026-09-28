INSERT INTO customers (
    id, email, first_name, last_name, country, city, is_active, signup_date
) VALUES
    (1, 'alice@example.com', 'Alice', 'Silva', 'Portugal', 'Porto', TRUE, '2025-01-10'),
    (2, 'bob@example.com', 'Bob', 'Santos', 'Portugal', 'Lisbon', TRUE, '2025-02-15'),
    (3, NULL, 'Charlie', 'Costa', 'Spain', NULL, TRUE, '2025-03-20'),
    (4, 'diana@example.com', 'Diana', 'Martins', 'Portugal', 'Braga', FALSE, '2025-04-05');

INSERT INTO products (
    id,
    sku,
    name,
    category,
    price,
    created_at,
    updated_at
) VALUES
(
    1,
    'LAPTOP-001',
    'Laptop Pro',
    'Electronics',
    1299.99,
    '2025-06-01 10:00:00+00',
    '2025-06-01 10:00:00+00'
),
(
    2,
    'MOUSE-001',
    'Wireless Mouse',
    'Electronics',
    29.99,
    '2025-06-02 10:00:00+00',
    '2025-06-04 08:00:00+00'
),
(
    3,
    'CHAIR-001',
    'Office Chair',
    'Furniture',
    249.50,
    '2025-06-03 10:00:00+00',
    '2025-06-06 14:00:00+00'
),
(
    4,
    'BOOK-001',
    'Data Engineering Book',
    'Books',
    49.90,
    '2025-06-04 10:00:00+00',
    '2025-06-08 16:00:00+00'
);

INSERT INTO orders (
    id, customer_id, status, payment_method, order_date
) VALUES
    (1, 1, 'completed', 'credit_card', '2025-06-01 10:30:00+00'),
    (2, 1, 'shipped', 'paypal', '2025-06-02 14:15:00+00'),
    (3, 2, 'pending', 'credit_card', '2025-06-03 09:00:00+00'),
    (4, 4, 'cancelled', 'debit_card', '2025-06-04 16:45:00+00');

INSERT INTO order_items (
    id, order_id, product_id, quantity, unit_price
) VALUES
    (1, 1, 1, 1, 1299.99),
    (2, 1, 2, 2, 29.99),
    (3, 2, 3, 1, 249.50),
    (4, 2, 4, 2, 49.90),
    (5, 3, 2, 1, 29.99),
    (6, 4, 4, 1, 49.90);

INSERT INTO shipments (
    id, order_id, carrier, shipped_at, delivered_at
) VALUES
    (1, 1, 'DHL', '2025-06-02 08:00:00+00', '2025-06-04 12:00:00+00'),
    (2, 2, 'CTT', '2025-06-03 10:00:00+00', NULL),
    (3, 4, 'UPS', NULL, NULL);

SELECT setval('customers_id_seq', (SELECT MAX(id) FROM customers));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));
SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items));
SELECT setval('shipments_id_seq', (SELECT MAX(id) FROM shipments));