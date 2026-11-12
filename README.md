# Ecommerce Data Platform

> **E-commerce data platform** supporting operational reporting and analytics. Incremental ingestion with checkpoints, data validation and quarantining, a medallion architecture using dbt, PostgreSQL warehouse and Apache Airflow orchestration.

[![CI](https://github.com/xavierkooijman/ecommerce-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xavierkooijman/ecommerce-data-platform/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/apache%20airflow-017CEE?style=flat-square&logo=apache-airflow&logoColor=white)](https://airflow.apache.org/)
[![dbt](https://img.shields.io/badge/dbt-FF0000?style=flat-square&logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

## Current capabilities
 
- [x] Incremental ingestion with PostgreSQL checkpoint store
- [x] Crash-safe checkpoint advancement (load + watermark in one transaction, integration-tested against real PostgreSQL)
- [x] PostgreSQL bronze landing layer with Docker Compose
- [x] Unit and integration tests (`pytest`, real PostgreSQL via `testcontainers`)
- [x] CI workflow on push and pull request: lint (`ruff`) and (`sqlfluff`), type check (`mypy`), tests (`pytest`)
- [x] Pydantic validation and record quarantine store
- [x] dbt: silver models, `dim_customers`, `dim_products`, `dim_date`, gold-layer facts
- [x] Airflow orchestration
- [x] Quarantine and pipeline runs monitoring
- [x] Alerting on pipeline and observability checks failures via webhook

## Technology stack
 
| Area | Selection |
|------|-----------|
| Language | Python 3.14 |
| Storage | PostgreSQL (source + warehouse) |
| Testing | `pytest`, `testcontainers` |
| Linting / typing | `ruff`, `mypy`, `sqlfluff` |
| Transformation | dbt |
| Orchestration | Apache Airflow |
| Containerization | Docker Compose |

## Quick start

> Prerequisites: uv, Docker Engine, Docker Compose and 8GB RAM available for Airflow.

Verify that uv and Docker are installed:

```bash
uv --version
docker --version
docker compose version
```

### 1. Clone the repository, install the dependencies and configure the environment variables
```bash
git clone https://github.com/xavierkooijman/ecommerce-data-platform.git
cd ecommerce-data-platform
uv sync
cp .env.example .env
```

### 2. Start all services(~2 minutes)
```bash
docker compose up -d --build
```

### 3. Seed source database with sample data and build date dimension
```bash
uv run python scripts/seed_source.py
uv run dbt build --project-dir dbt --select dim_date --indirect-selection cautious
```

Trigger DAGs in the Airflow UI at [http://localhost:8080](http://localhost:8080) 

See [docs/runbook.md](docs/runbook.md) for operational runbook.

## Testing
 
```bash
uv run pytest -v
```

### Airflow tests
```bash
docker build -t airflow-tests --target test .
docker run --rm airflow-tests
```

The tests cover data models and validation, checkpoint handling, ingestion and incremental extraction, PostgreSQL storage, quarantine management, pipeline tracking and observability checks, Airflow DAG loading and structure, and dbt transformations including Silver models, Gold dimensions and facts, and customer snapshots.

## Business Context

The business requirements and needs that drive architectural decisions are documented in [`docs/business-context.md`](docs/business-context.md).

## Architectural decisions

Architectural Decision Records are stored in [`docs/adr/`](docs/adr/).

## Attribution

Built as a public portfolio project by [@xavierkooijman](https://github.com/xavierkooijman) - Data Engineer. Sample data is synthetic for demonstration.

## License

MIT - see [LICENSE](LICENSE).