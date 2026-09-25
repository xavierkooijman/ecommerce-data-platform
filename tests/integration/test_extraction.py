from ecommerce_data_platform.extract.postgres import IncrementalPostgresExtractor

def test_extract_without_watermark_returns_all_rows(postgres_source_conn):
    extractor = IncrementalPostgresExtractor(postgres_source_conn)
    customers = extractor.extract("customers", None)
    assert len(customers) == 4

def test_extract_with_watermark_returns_only_newer_rows(postgres_source_conn):
    extractor = IncrementalPostgresExtractor(postgres_source_conn)
    products = extractor.extract("products", "2025-06-05")
    assert {product["id"] for product in products} == {3, 4}

def test_extract_with_future_watermark_returns_no_rows(postgres_source_conn):
    extractor = IncrementalPostgresExtractor(postgres_source_conn)
    products = extractor.extract("products", "2025-06-12")
    assert products == []

