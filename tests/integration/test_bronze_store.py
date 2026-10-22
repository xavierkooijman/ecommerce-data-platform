from ecommerce_data_platform.storage.postgres import PostgresBronzeStore


def test_read_returns_records_after_last_ingestion_id(
    warehouse_connection_factory,
    bronze_table,
):
    store = PostgresBronzeStore(warehouse_connection_factory)

    store.persist(bronze_table, [{"id": 1}, {"id": 2}, {"id": 3}])

    records = store.read(bronze_table, 1)

    assert len(records) == 2
    assert all(record.ingestion_id > 1 for record in records)


def test_read_returns_empty_list_when_no_new_records(
    warehouse_connection_factory,
    bronze_table,
):
    store = PostgresBronzeStore(warehouse_connection_factory)

    store.persist(bronze_table, [{"id": 1}, {"id": 2}, {"id": 3}])

    assert store.read(bronze_table, 999999) == []


def test_persist_and_read_returns_expected_records(
    warehouse_connection_factory,
    bronze_table,
):
    store = PostgresBronzeStore(warehouse_connection_factory)
    records = [{"id": 1}, {"id": 2}]

    assert store.persist(bronze_table, records) == 2

    retrieved = store.read(bronze_table, None)

    assert [record.payload for record in retrieved] == records