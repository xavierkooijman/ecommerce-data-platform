import os

import psycopg


def warehouse_connection() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("WAREHOUSE_DB_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_DB_PORT", "5433")),
        user="warehouse_user",
        password=os.environ["WAREHOUSE_DB_PASSWORD"],
        dbname="warehouse",
    )


def source_connection() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("SOURCE_DB_HOST", "localhost"),
        port=int(os.getenv("SOURCE_DB_PORT", "5432")),
        user="source_user",
        password=os.environ["SOURCE_DB_PASSWORD"],
        dbname="source",
    )