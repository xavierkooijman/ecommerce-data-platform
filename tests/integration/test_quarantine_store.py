
from ecommerce_data_platform.models import QuarantineStatus, RejectedRecord
from ecommerce_data_platform.storage.postgres import PostgresQuarantineStore


def test_persist_inserts_rejected_records(
    warehouse_connection_factory,
    data_source,
    bronze_table
):
    store = PostgresQuarantineStore(warehouse_connection_factory)

    store.persist(
        data_source,
        bronze_table,
        [
            RejectedRecord(
                ingestion_id=1,
                resource_pk="123",
                errors=[{"msg": "invalid"}],
            )
        ],
    )

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM meta.quarantine"
            )

            count = cur.fetchone()[0]

    assert count == 1


def test_persist_is_idempotent(
    warehouse_connection_factory,
    data_source,
    bronze_table
):
    store = PostgresQuarantineStore(warehouse_connection_factory)

    record = RejectedRecord(
        ingestion_id=1,
        resource_pk="123",
        errors=[{"msg": "invalid"}],
    )

    store.persist(data_source, bronze_table, [record])
    store.persist(data_source, bronze_table, [record])

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM meta.quarantine"
            )

            count = cur.fetchone()[0]

    assert count == 1

def test_resolve_updates_status(
    data_source,
    bronze_table,
    warehouse_connection_factory,
):
    store = PostgresQuarantineStore(warehouse_connection_factory)

    record = RejectedRecord(
        ingestion_id=1,
        resource_pk="123",
        errors=[{"msg": "invalid"}],
    )

    store.persist(data_source, bronze_table, [record])

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT quarantine_id FROM meta.quarantine"
            )

            quarantine_id = cur.fetchone()[0]

    store.resolve(
        quarantine_id,
        QuarantineStatus.REVALIDATED,
    )

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, resolved_at
                FROM meta.quarantine
                WHERE quarantine_id = %s
                """,
                (quarantine_id,),
            )

            status, resolved_at = cur.fetchone()

    assert status == QuarantineStatus.REVALIDATED
    assert resolved_at is not None

def test_get_open_quarantine_count(
    warehouse_connection_factory,
    data_source,
    bronze_table,
):
    store = PostgresQuarantineStore(warehouse_connection_factory)

    records = [
        RejectedRecord(
            ingestion_id=1,
            resource_pk="customer-1",
            errors=[{"msg": "invalid email"}],
        ),
        RejectedRecord(
            ingestion_id=2,
            resource_pk="customer-2",
            errors=[{"msg": "missing name"}],
        ),
    ]
    store.persist(data_source, bronze_table, records)

    assert store.get_open_quarantine_count() == 2

def test_get_oldest_open_quarantine_age_hours(
    warehouse_connection_factory,
    data_source,
    bronze_table,
):
    store = PostgresQuarantineStore(warehouse_connection_factory)

    store.persist(
        data_source,
        bronze_table,
        [
            RejectedRecord(
                ingestion_id=1,
                resource_pk="customer-1",
                errors=[{"msg": "invalid email"}],
            ),
            RejectedRecord(
                ingestion_id=2,
                resource_pk="customer-2",
                errors=[{"msg": "missing name"}],
            ),
        ],
    )

    with warehouse_connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE meta.quarantine
                SET quarantined_at = CASE ingestion_id
                    WHEN 1 THEN NOW() - INTERVAL '10 hours'
                    WHEN 2 THEN NOW() - INTERVAL '2 hours'
                END
                WHERE bronze_table = %s
                  AND ingestion_id IN (1, 2)
                """,
                (bronze_table,),
            )

    age_hours = store.get_oldest_open_quarantine_age_hours()

    assert 9.9 <= age_hours <= 10.1