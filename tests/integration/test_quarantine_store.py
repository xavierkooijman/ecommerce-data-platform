from ecommerce_data_platform.records import RejectedRecord
from ecommerce_data_platform.storage.postgres import PostgresQuarantineStore
from ecommerce_data_platform.types import QuarantineStatus


def test_persist_inserts_rejected_records(
    postgres_warehouse_conn,
):
    store = PostgresQuarantineStore(postgres_warehouse_conn)

    store.persist(
        "customers",
        [
            RejectedRecord(
                ingestion_id=1,
                source_pk="123",
                errors=[{"msg": "invalid"}],
            )
        ],
    )

    postgres_warehouse_conn.commit()

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM meta.quarantine"
        )

        count = cur.fetchone()[0]

    assert count == 1


def test_persist_is_idempotent(
    postgres_warehouse_conn,
):
    store = PostgresQuarantineStore(postgres_warehouse_conn)

    record = RejectedRecord(
        ingestion_id=1,
        source_pk="123",
        errors=[{"msg": "invalid"}],
    )

    store.persist("customers", [record])
    store.persist("customers", [record])

    postgres_warehouse_conn.commit()

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM meta.quarantine"
        )

        count = cur.fetchone()[0]

    assert count == 1

def test_resolve_updates_status(
    postgres_warehouse_conn,
):
    store = PostgresQuarantineStore(postgres_warehouse_conn)

    record = RejectedRecord(
        ingestion_id=1,
        source_pk="123",
        errors=[{"msg": "invalid"}],
    )

    store.persist("customers", [record])
    postgres_warehouse_conn.commit()

    with postgres_warehouse_conn.cursor() as cur:
        cur.execute(
            "SELECT quarantine_id FROM meta.quarantine"
        )

        quarantine_id = cur.fetchone()[0]

    store.resolve(
        quarantine_id,
        QuarantineStatus.REVALIDATED,
    )

    postgres_warehouse_conn.commit()

    with postgres_warehouse_conn.cursor() as cur:
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