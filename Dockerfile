FROM apache/airflow:3.3.2-python3.14

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/

USER root

WORKDIR /opt/airflow/ecommerce-data-platform

# Export the locked dependencies to a requirements.txt file, install airflow and then install the dependencies.
COPY --chown=airflow:root pyproject.toml uv.lock ./

RUN uv export \
        --locked \
        --no-dev \
        --group transform \
        --no-emit-project \
        --format requirements-txt \
        -o /tmp/requirements.txt \
    && uv pip install \
        --system \
        --no-cache \
        --constraint "/home/airflow/constraints.txt" \
        "apache-airflow==${AIRFLOW_VERSION}" \
    && uv pip install \
        --system \
        --no-cache \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /tmp/requirements.txt

# Add the src directory.
COPY --chown=airflow:root src/ ./src/

RUN uv pip install --system --no-deps .

USER airflow

# Add the dbt directory and its packages.
COPY --chown=airflow:root dbt/ ./dbt/

RUN cd dbt && dbt deps