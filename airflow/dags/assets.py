from airflow.sdk import Asset

ECOMMERCE_DB_CUSTOMERS_READY = Asset("ecommerce_db.customers.ready")
ECOMMERCE_DB_PRODUCTS_READY = Asset("ecommerce_db.products.ready")
ECOMMERCE_DB_ORDERS_READY = Asset("ecommerce_db.orders.ready")
ECOMMERCE_DB_ORDER_ITEMS_READY = Asset("ecommerce_db.order_items.ready")
ECOMMERCE_DB_SHIPMENTS_READY = Asset("ecommerce_db.shipments.ready")