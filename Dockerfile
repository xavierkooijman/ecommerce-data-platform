# base: Airflow + runtime deps + src (no dbt, no pytest)
FROM apache/airflow:3.3.2-python3.14 AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/

WORKDIR /opt/airflow/ecommerce_data_platform

COPY --chown=airflow:root pyproject.toml uv.lock ./

RUN uv export \
        --locked \
        --no-dev \
        --no-emit-project \
        --format requirements-txt \
        -o /tmp/requirements.txt \
    && uv pip install \
        --no-cache \
        --python "$(which python)" \
        --constraint "/home/airflow/constraints.txt" \
        "apache-airflow==${AIRFLOW_VERSION}" \
    && uv pip install \
        --no-cache \
        --python "$(which python)" \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /tmp/requirements.txt

COPY --chown=airflow:root src/ ./src/

RUN uv pip install --no-cache --python "$(which python)" --no-deps .


# test: base + pytest + dags + airflow tests
FROM base AS test

RUN uv pip install --no-cache --python "$(which python)" pytest

COPY --chown=airflow:root airflow/dags/ ./airflow/dags/
COPY --chown=airflow:root tests/airflow/ ./tests/airflow/

CMD ["python", "-m", "pytest", "tests/airflow", "-v"]


# runtime: base + dbt
FROM base AS runtime

RUN uv export \
        --locked \
        --no-dev \
        --group transform \
        --no-emit-project \
        --format requirements-txt \
        -o /tmp/requirements.txt \
    && uv pip install \
        --no-cache \
        --python "$(which python)" \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /tmp/requirements.txt

COPY --chown=airflow:root dbt/ ./dbt/

RUN cd dbt && dbt deps