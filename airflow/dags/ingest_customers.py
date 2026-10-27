from datetime import datetime, timedelta

from airflow.sdk import dag, task
from assets import ECOMMERCE_DB_CUSTOMERS_READY
from callbacks import webhook_task_failure_callback
from helpers import get_execution_context

from ecommerce_data_platform.extract.postgres import PostgresIncrementalExtractor
from ecommerce_data_platform.models import (
    BronzeTable,
    DataSource,
    PipelineStage,
    Resource,
    SourceSystem,
)
from ecommerce_data_platform.observability.pipeline_run_tracker import PipelineRunTracker
from ecommerce_data_platform.observability.source_checks_runner import run_source_checks
from ecommerce_data_platform.pipeline.ingestion import run_incremental_ingestion
from ecommerce_data_platform.pipeline.validation import run_bronze_validation
from ecommerce_data_platform.storage.postgres import (
    PostgresBronzeStore,
    PostgresCheckpointStore,
    PostgresPipelineRunStore,
    PostgresQuarantineStore,
)
from ecommerce_data_platform.utils.db import source_connection_factory, warehouse_connection_factory
from ecommerce_data_platform.validation.models import Customer

DATA_SOURCE = DataSource(SourceSystem.ECOMMERCE_DB, Resource.CUSTOMERS)
BRONZE_TABLE = BronzeTable.CUSTOMERS


@dag(
    dag_id="ingest_customers",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    on_failure_callback=webhook_task_failure_callback,
)
def customers_dag():
    @task
    def ingest_customers():
        run_incremental_ingestion(
            data_source=DATA_SOURCE,
            bronze_table=BRONZE_TABLE,
            extractor=PostgresIncrementalExtractor(source_connection_factory),
            bronze_store=PostgresBronzeStore(warehouse_connection_factory),
            checkpoint_store=PostgresCheckpointStore(warehouse_connection_factory),
            run_tracker=PipelineRunTracker(
                stage=PipelineStage.INGESTION,
                store=PostgresPipelineRunStore(warehouse_connection_factory),
                data_source=DATA_SOURCE,
                execution_context=get_execution_context()
            )
        )

    @task
    def validate_customers():
        run_bronze_validation(
            data_source=DATA_SOURCE,
            bronze_table=BRONZE_TABLE,
            model=Customer,
            bronze_store=PostgresBronzeStore(warehouse_connection_factory),
            checkpoint_store=PostgresCheckpointStore(warehouse_connection_factory),
            quarantine_store=PostgresQuarantineStore(warehouse_connection_factory),
            run_tracker=PipelineRunTracker(
                stage=PipelineStage.VALIDATION,
                store=PostgresPipelineRunStore(warehouse_connection_factory),
                data_source=DATA_SOURCE,
                execution_context=get_execution_context()
            )
        )

    @task(outlets=[ECOMMERCE_DB_CUSTOMERS_READY])
    def check_customer_alerts():
        run_source_checks(
            data_source=DATA_SOURCE,
            store=PostgresPipelineRunStore(warehouse_connection_factory)
        )

    ingest_customers() >> validate_customers() >> check_customer_alerts()

customers_dag()