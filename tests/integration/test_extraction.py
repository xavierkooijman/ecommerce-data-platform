from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor


def test_extract_without_watermark_returns_all_rows(patch_source_connection):
    customers = PostgresIncrementalExtractor().extract("customers", None)
    assert len(customers) == 4

def test_extract_with_watermark_returns_only_newer_rows(patch_source_connection):
    products = PostgresIncrementalExtractor().extract("products", "2025-06-05")
    assert {product["id"] for product in products} == {3, 4}

def test_extract_with_future_watermark_returns_no_rows(patch_source_connection):
    products = PostgresIncrementalExtractor().extract("products", "2025-06-12")
    assert products == []

