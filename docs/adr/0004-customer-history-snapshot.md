# ADR 0004: Customer History with dbt Snapshots

## Status

Accepted

## Context

The business needs historical customer attributes. For example, finance must know which country a customer was in when they placed an order, and how customer attributes changed over time. See [`docs/business-context.md`](../business-context.md).

Customers are ingested every 6 hours. Profile changes are rare and low-urgency.

## Decision

Customer history will be implemented using a dbt snapshot with the timestamp strategy. The snapshot will be stored in the Silver schema, alongside the other Silver models.

A Silver view named `customers` will provide the snapshot input. It will:

1. Read customer records from Bronze.
2. Exclude records that are quarantined.
3. Convert the JSONB payloads into typed columns.
4. Select the latest eligible record for each customer, ordered by `updated_at` descending and `ingestion_id` descending as a tie-breaker.

The snapshot will use the following configuration:

- **Unique key:** `id`
- **Strategy:** `timestamp`
- **Updated-at column:** `updated_at`
- **Schema:** `silver`
- **Hard deletes:** Ignored, since deletes are not currently captured by ingestion.

The timestamp strategy allows dbt to compare each customer's incoming `updated_at` value with the version already stored in the snapshot. When a newer version is detected, dbt expires the previous version and inserts the new one. Unchanged records do not create additional historical versions.

## Consequences

**Positive**

- Customer attribute history is retained without implementing custom SCD2 merge and version-management logic.
- dbt manages the expiration of previous versions and insertion of new versions.

**Negative**

- If a customer changes multiple times between snapshot runs, only the latest eligible state is captured. Intermediate states are lost.
- Snapshot history depends on the correctness and availability of the source `updated_at` value.

## Alternatives considered

1. **Maintain only the latest customer state:** This would be simpler, but it would not retain historical customer attributes.

2. **Process every Bronze version into a history table:** An incremental model could process each eligible Bronze record in order and maintain SCD2 validity intervals. This would preserve intermediate states, but would require custom logic for ordering, deduplication, late-arriving records and historical version management.

3. **Use dbt snapshots directly against all Bronze records:** Bronze can contain multiple records for the same customer. Passing those records directly to a snapshot would violate the expectation of one input row per unique key and could cause errors or unreliable results. Selecting the latest state before snapshotting avoids this issue.