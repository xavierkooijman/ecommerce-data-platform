
import sys
from pathlib import Path

import pytest

pytest.importorskip("airflow")
from airflow.models import DagBag

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DAG_DIR = PROJECT_ROOT / "airflow" / "dags"
sys.path.insert(0, str(DAG_DIR))


@pytest.fixture(scope="module")
def dag_bag() -> DagBag:
    return DagBag(dag_folder=str(DAG_DIR))


def get_loaded_dag(dag_bag: DagBag, dag_id: str):
    dag = dag_bag.dags.get(dag_id)
    assert dag is not None, f"DAG {dag_id!r} was not loaded"
    return dag


def test_dags_load(dag_bag: DagBag) -> None:
    assert dag_bag.import_errors == {}, (
        f"DAG import errors: {dag_bag.import_errors}"
    )


@pytest.mark.parametrize(
    ("dag_id", "tasks", "dependencies"),
    [
        (
            "ingest_customers",
            {"ingest_customers", "validate_customers"},
            {"validate_customers": {"ingest_customers"}},
        ),
        (
            "ingest_order_items",
            {"ingest_order_items", "validate_order_items"},
            {"validate_order_items": {"ingest_order_items"}},
        ),
        (
            "ingest_orders",
            {"ingest_orders", "validate_orders"},
            {"validate_orders": {"ingest_orders"}},
        ),
        (
            "ingest_products",
            {"ingest_products", "validate_products"},
            {"validate_products": {"ingest_products"}},
        ),
        (
            "ingest_shipments",
            {"ingest_shipments", "validate_shipments"},
            {"validate_shipments": {"ingest_shipments"}},
        ),
        ("transform_dimensions", {"build"}, {}),
        ("transform_orders", {"build"}, {}),
        ("transform_shipments", {"build"}, {}),
    ],
)
def test_dag_structure(
    dag_bag: DagBag,
    dag_id: str,
    tasks: set[str],
    dependencies: dict[str, set[str]],
) -> None:
    dag = get_loaded_dag(dag_bag, dag_id)

    assert set(dag.task_ids) == tasks

    for task_id, upstream_ids in dependencies.items():
        assert dag.get_task(task_id).upstream_task_ids == upstream_ids


@pytest.mark.parametrize(
    ("dag_id", "validate_task_id", "expected_asset_uri"),
    [
        (
            "ingest_customers",
            "validate_customers",
            "customers_ready",
        ),
        (
            "ingest_order_items",
            "validate_order_items",
            "order_items_ready",
        ),
        (
            "ingest_orders",
            "validate_orders",
            "orders_ready",
        ),
        (
            "ingest_products",
            "validate_products",
            "products_ready",
        ),
        (
            "ingest_shipments",
            "validate_shipments",
            "shipments_ready",
        ),
    ],
)
def test_validation_emits_expected_asset(
    dag_bag: DagBag,
    dag_id: str,
    validate_task_id: str,
    expected_asset_uri: str,
) -> None:
    """Each validation task must declare its expected asset outlet."""
    dag = get_loaded_dag(dag_bag, dag_id)

    validate_task = dag.get_task(validate_task_id)
    asset_uris = {asset.uri for asset in validate_task.outlets}

    assert expected_asset_uri in asset_uris