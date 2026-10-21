from ecommerce_data_platform.records import BronzeRecord
from ecommerce_data_platform.storage.postgres import PostgresBronzeReader


def test_read_returns_records_after_last_ingestion_id(
    postgres_warehouse_conn,
    patch_warehouse_connection,
):
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.customers (payload)
            VALUES ('{"id": 1}'),
                   ('{"id": 2}'),
                   ('{"id": 3}')
            """
        )
    records = PostgresBronzeReader().read("customers", 1)

    assert len(records) == 2
    assert all(record.ingestion_id > 1 for record in records)


def test_read_returns_empty_list_when_no_new_records(
    postgres_warehouse_conn,
    patch_warehouse_connection,
):
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.customers (payload)
            VALUES ('{"id": 1}'),
                   ('{"id": 2}'),
                   ('{"id": 3}')
            """
        )
    records = PostgresBronzeReader().read("customers", 999999)

    assert records == []


def test_read_returns_records_with_expected_format(
    postgres_warehouse_conn,
    patch_warehouse_connection,
):
    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.customers (payload)
            VALUES ('{"id": 1}'),
                   ('{"id": 2}'),
                   ('{"id": 3}')
            """
        )

    records = PostgresBronzeReader().read("customers", None)

    assert len(records) == 3
    assert all(isinstance(record, BronzeRecord) for record in records)