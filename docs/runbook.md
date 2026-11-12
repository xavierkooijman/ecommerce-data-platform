# Operations Runbook

## Pipeline Overview

| Stage | Component | Failure signal |
|---|---|---|
| Ingestion | `scripts/ingestion.py` | Extraction failure, database error, unexpected zero rows |
| Validation | `scripts/validation.py` | Validation errors, rejected records, quarantined records |
| Transformation | dbt Silver and Gold models | dbt build or data test failure |
| Observability | `scripts/observability.py` | Global or per-source check triggered |
| Orchestration | Airflow DAGs | DAG run failed / retries exhausted |

The ingestion and validation stages are resource-oriented: you can execute them independently for any supported combination of source system and resource. The same applies to the per-source observability checks.

Supported source systems:
- `ecommerce_db`

Supported resources:

- `customers`
- `products`
- `orders`
- `order_items`
- `shipments`

## Ingestion

Ingestion extracts data from a specified source system and resource, tracks incremental progress using watermarks, and loads extracted records into the Bronze layer.

Run ingestion independently for each resource:

```bash
uv run python scripts/ingestion.py \
    --source-system ecommerce_db \
    --resource customers
```

The same command can be used with other configured source systems and their respective resources.

### Example: Run all ecommerce resources

```bash
uv run python scripts/ingestion.py --source-system ecommerce_db --resource customers
uv run python scripts/ingestion.py --source-system ecommerce_db --resource products
uv run python scripts/ingestion.py --source-system ecommerce_db --resource orders
uv run python scripts/ingestion.py --source-system ecommerce_db --resource order_items
uv run python scripts/ingestion.py --source-system ecommerce_db --resource shipments
```

## Validation

Validation runs ingested Bronze records against the validation models defined for each source system and resource.

```bash
uv run python scripts/validation.py \
    --source-system ecommerce_db \
    --resource customers
```

### Example: Validate all ecommerce resources

```bash
uv run python scripts/validation.py --source-system ecommerce_db --resource customers
uv run python scripts/validation.py --source-system ecommerce_db --resource products
uv run python scripts/validation.py --source-system ecommerce_db --resource orders
uv run python scripts/validation.py --source-system ecommerce_db --resource order_items
uv run python scripts/validation.py --source-system ecommerce_db --resource shipments
```

Validation identifies records that do not satisfy their respective data models. Invalid records are quarantined.

## Transformation

Transformations are performed using dbt, with separate Airflow DAGs for dimensions, orders, and shipments.

These DAGs are triggered by data asset updates. They build the relevant models when their upstream ingestion dependencies are satisfied.

### Dimensions

**DAG:** `transform_dimensions`

**Trigger:** Customers OR products ready.

Builds the following models and their selected downstream dependencies:

- `customers`
- `products`
- `customers_snapshot`
- `dim_customer`
- `dim_product`

Command:

```bash
uv run dbt build --project-dir dbt \
    --select customers products customers_snapshot dim_customer dim_product \
    --indirect-selection cautious
```

The cautious indirect selection strategy controls which indirectly selected tests are included in the build.

### Orders

**DAG:** `transform_orders`

**Trigger:** Orders AND order items ready.

Builds:

- `orders`
- `order_items`
- `fct_order_fulfillment`
- `fct_item_sales`

Command:

```bash
uv run dbt build --project-dir dbt \
    --select orders order_items fct_order_fulfillment fct_item_sales
```

### Shipments

**DAG:** `transform_shipments`

**Trigger:** Shipments ready.

Builds:

- `shipments`

Command:

```bash
uv run dbt build --project-dir dbt --select shipments
```

### Manual transformation

To execute the entire dbt project manually, including models and tests:

```bash
uv run dbt build --project-dir dbt
```

Review the dbt output for failed models and tests.

## Observability

Observability checks monitor pipeline execution, data quality and quarantine health.

There are two categories of checks: global checks and per-source checks.

### Global checks

Global checks monitor the overall health of the platform, independently of an individual source system or resource.

Execute them with:

```bash
uv run python scripts/observability.py global-checks
```


| Check | What it monitors |
|---|---|
| `open_quarantine_count` | Total number of quarantine records still awaiting resolution. Triggers when the count reaches the configured threshold. |
| `oldest_open_quarantine_age_hours` | Age in hours of the oldest unresolved quarantine record. Triggers when it reaches the configured threshold. |
| `stuck_runs` | Number of pipeline runs that have remained in progress beyond the configured maximum time. Triggers when at least one stuck run exists. |

### Per-source checks

Per-source checks monitor the execution and quality of an individual source system and resource combination.

Execute them with:

```bash
uv run python scripts/observability.py source-checks \
    --source-system ecommerce_db \
    --resource customers
```

| Check | What it monitors |
|---|---|
| `consecutive_zero_row_runs` | Number of consecutive successful pipeline runs that extracted zero rows. Triggers when the count reaches the configured threshold. |
| `rejection_rate_percentage` | Percentage of inspected records rejected during the latest run. Triggers when the percentage reaches the configured threshold. |

### Example: Check all ecommerce resources

```bash
uv run python scripts/observability.py source-checks --source-system ecommerce_db --resource customers
uv run python scripts/observability.py source-checks --source-system ecommerce_db --resource products
uv run python scripts/observability.py source-checks --source-system ecommerce_db --resource orders
uv run python scripts/observability.py source-checks --source-system ecommerce_db --resource order_items
uv run python scripts/observability.py source-checks --source-system ecommerce_db --resource shipments
```

## Seed Source Database

The source database can be populated using the seed script.

Run with default configuration:

```bash
uv run python scripts/seed_source.py
```

Custom configuration:

```bash
uv run python scripts/seed_source.py \
    --seed 42 \
    --customers 2000 \
    --products 300 \
    --orders 12000
```

## Full pipeline reset

**Warning:** This operation destroys persisted Docker volume data, including source and warehouse database.

```bash
docker compose down -v
docker compose up -d
uv run python scripts/seed_source.py
```
