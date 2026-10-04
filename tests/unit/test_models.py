from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ecommerce_data_platform.validation.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    Product,
    Shipment,
)


def test_customer_accepts_valid_data():
    customer = Customer(
        id=1,
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        country="Portugal",
        city="Porto",
        is_active=True,
        signup_date=date(2026, 1, 1),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0),
    )

    assert customer.email == "john@example.com"
    assert customer.city == "Porto"


def test_customer_accepts_null_city():
    customer = Customer(
        id=1,
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        country="Portugal",
        city=None,
        is_active=True,
        signup_date=date(2026, 1, 1),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0),
    )

    assert customer.city is None


def test_customer_rejects_invalid_email():
    with pytest.raises(ValidationError):
        Customer(
            id=1,
            email="not-an-email",
            first_name="John",
            last_name="Doe",
            country="Portugal",
            city="Porto",
            is_active=True,
            signup_date=date(2026, 1, 1),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_product_accepts_valid_data():
    product = Product(
        id=1,
        sku="SKU-001",
        name="Laptop",
        category="Electronics",
        price=Decimal("999.99"),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0),
    )

    assert product.price == Decimal("999.99")


def test_product_rejects_negative_price():
    with pytest.raises(ValidationError):
        Product(
            id=1,
            sku="SKU-001",
            name="Laptop",
            category="Electronics",
            price=Decimal("-1.00"),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_order_accepts_valid_data():
    order = Order(
        id=1,
        customer_id=10,
        status=OrderStatus.PROCESSING,
        payment_method=PaymentMethod.CREDIT_CARD,
        order_date=datetime(2026, 1, 1, 10, 0),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0),
    )

    assert order.status is OrderStatus.PROCESSING
    assert order.payment_method is PaymentMethod.CREDIT_CARD


def test_order_rejects_invalid_status():
    with pytest.raises(ValidationError):
        Order(
            id=1,
            customer_id=10,
            status="invalid",
            payment_method=PaymentMethod.CREDIT_CARD,
            order_date=datetime(2026, 1, 1, 10, 0),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_order_rejects_invalid_payment_method():
    with pytest.raises(ValidationError):
        Order(
            id=1,
            customer_id=10,
            status=OrderStatus.PROCESSING,
            payment_method="bitcoin",
            order_date=datetime(2026, 1, 1, 10, 0),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_order_item_accepts_valid_data():
    order_item = OrderItem(
        id=1,
        order_id=10,
        product_id=20,
        quantity=2,
        unit_price=Decimal("49.99"),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0),
    )

    assert order_item.quantity == 2
    assert order_item.unit_price == Decimal("49.99")


def test_order_item_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        OrderItem(
            id=1,
            order_id=10,
            product_id=20,
            quantity=-1,
            unit_price=Decimal("49.99"),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_order_item_rejects_negative_unit_price():
    with pytest.raises(ValidationError):
        OrderItem(
            id=1,
            order_id=10,
            product_id=20,
            quantity=2,
            unit_price=Decimal("-1.00"),
            created_at=datetime(2026, 1, 1, 10, 0),
            updated_at=datetime(2026, 1, 2, 10, 0),
        )


def test_shipment_accepts_valid_data():
    shipment = Shipment(
        id=1,
        order_id=10,
        carrier="DHL",
        shipped_at=datetime(2026, 1, 2, 10, 0),
        delivered_at=datetime(2026, 1, 4, 10, 0),
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 4, 10, 0),
    )

    assert shipment.carrier == "DHL"


def test_shipment_accepts_null_dates():
    shipment = Shipment(
        id=1,
        order_id=10,
        carrier="DHL",
        shipped_at=None,
        delivered_at=None,
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 1, 10, 0),
    )

    assert shipment.shipped_at is None
    assert shipment.delivered_at is None