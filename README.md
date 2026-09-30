# Ecommerce Data Platform

> **E-commerce data platform** supporting operational reporting and analytics. PostgreSQL ingestion with watermark checkpoints, data validation, a bronze/silver/gold warehouse (dbt), and Airflow orchestration - built as a learning/reference implementation of data engineering patterns.

[![CI](https://github.com/xavierkooijman/ecommerce-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xavierkooijman/ecommerce-data-platform/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

## Problem

As source data grows and changes continuously, repeatedly processing entire tables becomes inefficient, while reporting still requires reasonably fresh and trustworthy data.

This project explores a reference implementation for:

- **Incremental ingestion** that can resume from a persisted watermark without unnecessarily reprocessing previously ingested records
- **Failure-safe processing** where loading data and advancing the ingestion checkpoint succeed or fail together
- **Separation of concerns** between raw landing, validation, transformation, and analytics-ready data so each stage can be tested independently
- **Data quality handling** that prevents invalid source records from silently propagating into downstream datasets

## Data Source

A synthetic OLTP PostgreSQL database containing `customers`, `products`, `orders`, `order_items`, and `shipments`.

The dataset is generated to represent an operational e-commerce system with realistic update patterns and temporal behaviour, including:

- Customers and products being updated after their initial creation
- Orders progressing through their lifecycle over time
- Shipments and delivery events arriving after the corresponding orders
- Different tables changing at different rates
- Seasonal increases in order volume around Black Friday, Christmas, and summer sales
- Late-arriving updates that require downstream pipelines to account for changes to previously ingested records

See [`seed/generate_seed_data.py`](seed/generate_seed_data.py).

## Current capabilities
 
- [x] Incremental ingestion with PostgreSQL checkpoint store
- [x] Crash-safe checkpoint advancement (load + watermark in one transaction, integration-tested against real PostgreSQL)
- [x] PostgreSQL bronze landing layer with Docker Compose
- [x] Unit and integration tests (`pytest`, real PostgreSQL via `testcontainers`)
- [x] CI workflow on push and pull request: lint (`ruff`), type check (`mypy`), tests (`pytest`)
- [ ] Pydantic validation and record quarantine / dead-letter store
- [ ] dbt: staging models, `dim_customers`, `dim_products`, `dim_date`, gold-layer facts
- [ ] Airflow orchestration

## Technology stack
 
| Area | Selection |
|------|-----------|
| Language | Python 3.14 |
| Storage | PostgreSQL (source + warehouse) |
| Testing | `pytest`, `testcontainers` |
| Linting / typing | `ruff`, `mypy` |
| Transformation (planned) | dbt |
| Orchestration (planned) | Apache Airflow |
| Containerization | Docker Compose |


## Testing
 
```bash
uv run pytest -v
```
 
Coverage includes: incremental extraction (with/without a watermark, future-watermark edge case), checkpoint persistence, and crash-safety of the load+checkpoint transaction against a real Postgres instance via `testcontainers`.

## Business Context

The business requirements and needs that drive architectural decisions are documented in [`docs/business-context.md`](docs/business-context.md).

## Engineering decisions

Architectural Decision Records are stored in [`docs/adr/`](docs/adr/).

## Attribution

Built as a public portfolio project by [@xavierkooijman](https://github.com/xavierkooijman) - Data Engineer. Sample data is synthetic for demonstration.

## License

MIT - see [LICENSE](LICENSE).