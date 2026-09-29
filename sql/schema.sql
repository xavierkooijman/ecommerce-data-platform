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

CREATE TABLE IF NOT EXISTS meta.pipeline_checkpoints (
    pipeline_name TEXT PRIMARY KEY,
    watermark TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);