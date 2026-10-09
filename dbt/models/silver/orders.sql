{{ config(
    materialized='incremental',
    unique_key='id'
) }}

with bronze as (
    select
        ingestion_id,
        payload
    from {{ source('bronze', 'orders') }}

    {% if is_incremental() %}
        where ingestion_id >(
            select
                coalesce(max(bronze_ingestion_id), 0)
            from {{ this }}
        )
    {% endif %}
),

validated as (
    select b.*
    from bronze as b
    left join {{ source('meta', 'quarantine') }} as q
        on
            q.source_table = 'orders'
            and b.ingestion_id = q.ingestion_d
    where q.quarantine_id is null
),

typed as (
    select
        ingestion_id as bronze_ingestion_id,
        (payload ->> 'id')::int as id,
        (payload ->> 'customer_id')::int as customer_id,
        payload ->> 'status' as status,
        payload ->> 'payment_method' as payment_method,
        (payload ->> 'order_date')::timestamptz as order_date,
        (payload ->> 'created_at')::timestamptz as created_at,
        (payload ->> 'updated_at')::timestamptz as updated_at
    from validated
),

ranked as (
    select
        *,
        row_number() over (
            partition by id
            order by updated_at desc, bronze_ingestion_id desc
        ) as rn
    from typed
),

latest as (
    select
        r.bronze_ingestion_id,
        r.id,
        r.customer_id,
        r.status,
        r.payment_method,
        r.order_date,
        r.created_at,
        r.updated_at
    from ranked as r
    {% if is_incremental() %}
    left join {{ this }} t
        on t.id = r.id
    where r.rn = 1 
        and (t.id is null or r.updated_at > t.updated_at)
    {% else %}
        where r.rn = 1
    {% endif %}
)

select *
from latest
