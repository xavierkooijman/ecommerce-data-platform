{{ config(materialized='view') }}

with bronze as (
    select
        ingestion_id,
        payload
    from {{ source('bronze', 'customers') }}
),

validated as (
    select b.*
    from bronze as b
    left join {{ source('meta', 'quarantine') }} as q
        on
            q.source_table = 'customers'
            and b.ingestion_id = q.ingestion_id
    where q.quarantine_id is null
),

typed as (
    select
        ingestion_id as bronze_ingestion_id,
        (payload ->> 'id')::int as customer_id,
        payload ->> 'email' as email,
        payload ->> 'first_name' as first_name,
        payload ->> 'last_name' as last_name,
        payload ->> 'country' as country,
        payload ->> 'city' as city,
        (payload ->> 'is_active')::boolean as is_active,
        (payload ->> 'signup_date')::date as signup_date,
        (payload ->> 'created_at')::timestamptz as created_at,
        (payload ->> 'updated_at')::timestamptz as updated_at
    from validated
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by updated_at desc, bronze_ingestion_id desc
        ) as rn
    from typed
)

select
    bronze_ingestion_id,
    customer_id,
    email,
    first_name,
    last_name,
    country,
    city,
    is_active,
    signup_date,
    created_at,
    updated_at
from ranked
where rn = 1
