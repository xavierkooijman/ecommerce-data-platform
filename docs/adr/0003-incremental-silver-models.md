# ADR 0003: Incremental Silver Models

## Status

Accepted

## Context

The Bronze layer stores raw source records as JSONB payloads, with an `ingestion_id` assigned to each ingested record. Multiple Bronze records can represent successive states of the same business entity.

The Silver layer needs to convert these payloads into typed, queryable tables while maintaining the latest known state of each entity. Reprocessing the full Bronze history on every run would be unnecessary as Bronze grows.

Records that have been quarantined by the validation process must also be excluded from Silver processing.

The source `updated_at` timestamp represents the business record's last modification time. A newly ingested record should not replace a newer state already stored in Silver simply because it arrived later.

## Decision

Products, orders, order items and shipments will use dbt incremental models with the `merge` incremental strategy and the business entity's `id` as the unique key.

Each model will follow the same processing pattern:

1. **Read new Bronze records:** On incremental runs, select records whose `ingestion_id` is greater than the maximum `bronze_ingestion_id` already stored in the corresponding Silver table. On the initial run, read the full Bronze source.
2. **Exclude quarantined records:** Left join the Bronze records to `meta.quarantine` using the source table name and `ingestion_id`, then exclude records with a matching quarantine entry.
3. **Convert payloads into typed columns:** Extract the fields from the JSONB payload and cast them to their expected SQL types.
4. **Rank records by business key:** Use `row_number()` partitioned by `id`, ordered by `updated_at` descending and `bronze_ingestion_id` descending. This selects the latest incoming record for each entity, using the ingestion ID as a tie-breaker when timestamps match.
5. **Compare incoming records with Silver:** On incremental runs, left join the ranked records to the existing Silver table by `id`. Keep only the latest incoming record for each entity when either:
   - No matching entity exists in Silver; or
   - The incoming `updated_at` is strictly greater than the current Silver `updated_at`.

6. **Merge into Silver:** dbt merges the selected records using `id` as the unique key, inserting new entities and updating existing entities with newer source states.

On the initial run, the models select the latest eligible record per entity without comparing against an existing Silver table.

The four models are:

- `silver.products`
- `silver.orders`
- `silver.order_items`
- `silver.shipments`

## Consequences

**Positive**

- Silver processes newly ingested Bronze records instead of scanning the entire Bronze history on every incremental run.
- Quarantined records are excluded from downstream Silver processing.
- Multiple incoming records for the same entity are reduced to one candidate before the merge.
- Older source states cannot overwrite newer Silver states, even if they are ingested later.
- The implementation uses standard SQL transformations and dbt's built-in merge strategy without requiring a custom incremental strategy.
- The models retain the `bronze_ingestion_id` associated with the selected source state, allowing subsequent runs to identify the ingestion boundary.

**Negative**

- The incremental filter depends on the maximum `bronze_ingestion_id` stored in Silver. If a Bronze record is skipped because it is quarantined, it will not automatically be reconsidered by these models when that quarantine record is later resolved, because its ingestion ID may already fall behind the Silver boundary.
- The models preserve only the latest state. Intermediate changes between processing runs are not retained in Silver.
- Ranking and comparing timestamps adds query complexity.
- The models rely on `updated_at` being the source of truth for the business record's last modification time.
- Correct incremental processing depends on `ingestion_id` being a reliable indicator of ingestion order.
- Resolved quarantined records are not automatically reprocessed by the Silver models.

## Alternatives considered

1. **Full refresh on every run:** Rebuild Silver from all eligible Bronze records each time. This is simpler to reason about, but repeats work as Bronze grows.

2. **Merge all newly ingested records without ranking:** Multiple incoming rows may share the same unique key in a single merge input. Selecting the latest candidate per entity avoids ambiguous updates and potential merge errors.

3. **Update Silver whenever a record has a higher `ingestion_id`:** This would treat ingestion order as the source of truth. A late-arriving record with an older `updated_at` could then overwrite a newer business state.

4. **Maintain a separate checkpoint for each Silver model:** This would make processing progress explicit and independent of the Silver data. The current implementation instead uses the maximum `bronze_ingestion_id` in Silver to keep the design simpler.