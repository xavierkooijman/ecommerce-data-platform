CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS bronze.customers (
    ingestion_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.products (
    ingestion_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.orders (
    ingestion_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.order_items (
    ingestion_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.shipments (
    ingestion_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS meta.checkpoints (
    stage TEXT NOT NULL,
    source_table TEXT NOT NULL,
    checkpoint_ts TIMESTAMPTZ,
    checkpoint_num BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (stage, source_table),
    CHECK( num_nonnulls(checkpoint_ts, checkpoint_num) = 1 )
);

CREATE TABLE IF NOT EXISTS meta.quarantine (
    quarantine_id BIGSERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    ingestion_id BIGINT NOT NULL,
    source_pk TEXT,
    errors JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'revalidated', 'superseded', 'wont_fix')),
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    UNIQUE (source_table, ingestion_id),
    CHECK (
        (status = 'open' AND resolved_at IS NULL)
        OR (status != 'open' AND resolved_at IS NOT NULL)
    )
);