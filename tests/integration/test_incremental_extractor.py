from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.models import Resource


def test_extract_without_watermark_returns_all_rows(source_connection_factory):
    customers = PostgresIncrementalExtractor(source_connection_factory).extract(
        Resource.CUSTOMERS, None
    )
    assert len(customers) == 4

def test_extract_with_watermark_returns_only_newer_rows(source_connection_factory):
    products = PostgresIncrementalExtractor(source_connection_factory).extract(
        Resource.PRODUCTS, "2025-06-05"
    )
    assert {product["id"] for product in products} == {3, 4}

def test_extract_with_future_watermark_returns_no_rows(source_connection_factory):
    products = PostgresIncrementalExtractor(source_connection_factory).extract(
        Resource.PRODUCTS, "2025-06-12"
    )
    assert products == []

