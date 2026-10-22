{{ config(
    unique_key='order_item_id',
    incremental_strategy='merge',
) }}

with bronze as (
    select
        ingestion_id,
        payload
    from {{ source('bronze', 'order_items') }}

    {% if is_incremental() %}
        where ingestion_id > (
            select coalesce(max(t.bronze_ingestion_id), 0)
            from {{ this }} as t
        )
    {% endif %}
),

validated as (
    select b.*
    from bronze as b
    left join {{ source('meta', 'quarantine') }} as q
        on
            q.bronze_table = 'order_items'
            and b.ingestion_id = q.ingestion_id
    where q.quarantine_id is null
),

typed as (
    select
        ingestion_id as bronze_ingestion_id,
        (payload ->> 'id')::int as order_item_id,
        (payload ->> 'order_id')::int as order_id,
        (payload ->> 'product_id')::int as product_id,
        (payload ->> 'quantity')::int as quantity,
        (payload ->> 'unit_price')::numeric(10, 2) as unit_price,
        (payload ->> 'created_at')::timestamptz as created_at,
        (payload ->> 'updated_at')::timestamptz as updated_at
    from validated
),

ranked as (
    select
        *,
        row_number() over (
            partition by order_item_id
            order by updated_at desc, bronze_ingestion_id desc
        ) as rn
    from typed
),

latest as (
    select
        r.bronze_ingestion_id,
        r.order_item_id,
        r.order_id,
        r.product_id,
        r.quantity,
        r.unit_price,
        r.created_at,
        r.updated_at
    from ranked as r
    {% if is_incremental() %}
        left join {{ this }} as t
            on r.order_item_id = t.order_item_id
        where
            r.rn = 1
            and (
                t.order_item_id is null
                or r.updated_at > t.updated_at
                or (
                    r.updated_at = t.updated_at
                    and r.bronze_ingestion_id > t.bronze_ingestion_id
                )
            )
    {% else %}
        where r.rn = 1
    {% endif %}
)

select *
from latest
