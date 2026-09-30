# ADR 0001: Incremental ingestion with PostgreSQL watermarks

## Status

Accepted

## Context

The platform ingests data from an operational PostgreSQL database containing customers, products, orders, order items, and shipments.

The business requires different ingestion frequencies for these tables, ranging from every 5 minutes for orders and order items to every 6 hours for customers and products. Re-extracting complete tables on every run would become increasingly inefficient as the source dataset grows.

The ingestion pipeline must therefore:

- Extract only records that have changed since the previous successful run
- Resume from the last successfully processed position after an interruption
- Avoid advancing the checkpoint when loading the extracted records fails
- Support different ingestion cadences and independently track progress for each table
- Persist extracted records before advancing the checkpoint

The source tables contain an `updated_at` timestamp that changes when an existing record is modified, providing a suitable watermark for incremental extraction.

## Decision

Use an `updated_at` timestamp watermark for incremental extraction and store the latest successfully processed watermark in a PostgreSQL metadata table.

Each source table has its own checkpoint identified by its pipeline/table name.

For each ingestion run:

1. Read the previously stored watermark.
2. If no watermark exists, perform an initial full extraction.
3. Otherwise, extract records where `updated_at` is greater than the stored watermark.
4. Persist the extracted records to the PostgreSQL Bronze landing layer.
5. Determine the maximum `updated_at` from the extracted records.
6. Update the checkpoint to that value.
7. Commit the landing data and checkpoint update as one transaction.

If the landing operation or checkpoint update fails, the transaction is rolled back and the previous checkpoint is retained.

The Bronze layer stores the extracted source records as JSONB payloads, preserving the source representation before downstream transformation and modelling.

## Consequences

**Positive**

- Incremental runs transfer only records changed since the previous successful run.
- Checkpoints are durable and shared through PostgreSQL rather than local files.
- Each table can progress independently according to its own freshness requirement.
- Landing data and checkpoint advancement are transactionally consistent.
- A failed run does not advance the checkpoint, allowing the affected records to be retried.
- The approach is simple to operate with the existing PostgreSQL-based architecture.
- The Bronze layer preserves the extracted source records before downstream transformations.

**Negative**

- The approach depends on reliable `updated_at` values in the source system.
- Changes that do not update the watermark column will not be detected.
- Records with an `updated_at` value older than the stored watermark cannot be captured by the incremental query.
- Hard deletes are not captured because deleting a source row does not produce an updated_at value for the extractor to observe.
- The checkpoint metadata and Bronze landing layer currently share the same PostgreSQL instance, coupling pipeline state to the landing infrastructure.

## Alternatives considered

1. **Full table extraction on every run** — rejected because it does not scale with increasing source-table size and unnecessarily reprocesses unchanged records.

2. **File-based checkpoints** — rejected because the pipeline already depends on PostgreSQL for landing and metadata, making a database-backed checkpoint more appropriate for durable and shared pipeline state.

3. **Change Data Capture (CDC)** — deferred because the current project only requires incremental extraction based on source updates. CDC would introduce additional infrastructure and operational complexity that is not required at this stage.
