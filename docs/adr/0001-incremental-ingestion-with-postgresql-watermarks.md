# ADR 0001: Incremental ingestion with PostgreSQL watermarks

## Status

Accepted

## Context

The platform ingests data from an operational PostgreSQL database containing customers, products, orders, order items, and shipments.

The business requires different ingestion frequencies for these tables, ranging from every 5 minutes for orders and order items to every 6 hours for customers and products. Re-extracting complete tables on every run would become increasingly inefficient as the source dataset grows.

The ingestion pipeline must therefore:

- Extract only records that have changed since the previous successful run
- Resume from the last successfully processed position after an interruption
- Support different ingestion cadences and independently track progress for each table
- Persist extracted records before advancing the checkpoint

The source tables contain an `updated_at` timestamp that changes when an existing record is modified, providing a suitable watermark for incremental extraction.

## Decision

Use an `updated_at` timestamp watermark for incremental extraction and store the latest successfully processed watermark in a PostgreSQL metadata table.

Each source table has its own checkpoint identified by its pipeline/table name.

For each ingestion run:

1. Read the previously stored watermark.
2. If no watermark exists, perform an initial full extraction.
3. Otherwise, extract records where `updated_at` is greater than or equal to the stored watermark.
4. Persist the extracted records to the PostgreSQL Bronze landing layer.
5. Determine the maximum `updated_at` from the extracted records.
6. Update the checkpoint to that value.

The Bronze layer stores the extracted source records as JSONB payloads, preserving the source representation before downstream transformation and modelling.

## Consequences

**Positive**

- Incremental runs transfer only records changed since the previous successful run.
- Each table can progress independently according to its own cadence.
- The Bronze layer preserves the extracted source records before downstream transformations.

**Negative**

- The approach depends on reliable `updated_at` values in the source system.
- Changes that do not update the watermark column will not be detected.
- Records with an `updated_at` value older than the stored watermark cannot be captured by the incremental extractor.
- Hard deletes are not captured because deleting a source row does not produce an updated_at value for the extractor to observe.

## Alternatives considered

1. **Full table extraction on every run** — rejected because it does not scale with increasing source table size and unnecessarily reprocesses unchanged records.

2. **Change Data Capture (CDC)** — deferred because the current project only requires incremental extraction based on source updates. CDC would introduce additional infrastructure and operational complexity that is not required.
