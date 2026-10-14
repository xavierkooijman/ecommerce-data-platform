with products as (
    select
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_sk,
        product_id,
        sku,
        product_name,
        category,
        price
    from {{ ref('products') }}
),

unknown_product as (
    select
        '-1'::text as product_sk,
        -1::int as product_id,
        'unknown'::text as sku,
        'unknown'::text as product_name,
        'unknown'::text as category,
        0::numeric(10, 2) as price
)

select *
from products
union all
select *
from unknown_product
