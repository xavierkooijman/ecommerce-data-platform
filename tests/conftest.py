from pathlib import Path

import psycopg
import pytest
import yaml
from testcontainers.community.postgres import PostgresContainer

PROJECT_ROOT = Path(__file__).parents[1]
SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"
SOURCE_SCHEMA_FILE = PROJECT_ROOT / "init-db" / "source_schema.sql"
SOURCE_SEED_FILE = PROJECT_ROOT / "tests" / "fixtures" / "seed_source.sql"

@pytest.fixture(scope="session")
def postgres_source_container():
    with PostgresContainer("postgres:18") as container:
        yield container

@pytest.fixture(scope="session")
def postgres_warehouse_container():
    with PostgresContainer("postgres:18") as container:
        yield container

@pytest.fixture
def postgres_source_conn(postgres_source_container):
    conn = psycopg.connect(
        host=postgres_source_container.get_container_host_ip(),
        port=postgres_source_container.get_exposed_port(5432),
        user=postgres_source_container.username,
        password=postgres_source_container.password,
        dbname=postgres_source_container.dbname,
    )
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        cur.execute(SOURCE_SCHEMA_FILE.read_text())
        cur.execute(SOURCE_SEED_FILE.read_text(), prepare=False)
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def postgres_warehouse_conn(postgres_warehouse_container):
    conn = psycopg.connect(
        host=postgres_warehouse_container.get_container_host_ip(),
        port=postgres_warehouse_container.get_exposed_port(5432),
        user=postgres_warehouse_container.username,
        password=postgres_warehouse_container.password,
        dbname=postgres_warehouse_container.dbname,
    )

    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS bronze CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS meta CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS silver CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS gold CASCADE;")
        cur.execute(SCHEMA_FILE.read_text())
    conn.commit()

    yield conn
    conn.close()

@pytest.fixture(scope="session")
def dbt_profile(postgres_warehouse_container, tmp_path_factory):
    container = postgres_warehouse_container

    profile = {
        "ecommerce_data_platform": {
            "target": "test",
            "outputs": {
                "test": {
                    "type": "postgres",
                    "host": container.get_container_host_ip(),
                    "port": int(container.get_exposed_port(5432)),
                    "user": container.username,
                    "pass": container.password,
                    "dbname": container.dbname,
                    "schema": "dbt_test",
                    "threads": 2,
                }
            },
        }
    }

    profiles_dir = tmp_path_factory.mktemp("dbt_profiles")
    (profiles_dir / "profiles.yml").write_text(
        yaml.safe_dump(profile)
    )

    return profiles_dir