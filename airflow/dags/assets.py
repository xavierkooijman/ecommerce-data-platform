from airflow.sdk import Asset

CUSTOMERS_READY = Asset("customers_ready")
PRODUCTS_READY = Asset("products_ready")
ORDERS_READY = Asset("orders_ready")
ORDER_ITEMS_READY = Asset("order_items_ready")
SHIPMENTS_READY = Asset("shipments_ready")