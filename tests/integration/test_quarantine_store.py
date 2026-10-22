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