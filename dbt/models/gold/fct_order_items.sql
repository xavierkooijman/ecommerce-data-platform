select
    {{ dbt_utils.generate_surrogate_key(['order_item_id']) }} as order_item_sk,
    oi.order_item_id,
    oi.order_id,
    coalesce(c.customer_sk, '-1') as customer_sk,
    coalesce(p.product_sk, '-1') as product_sk,
    oi.quantity,
    oi.unit_price,
    d.date_sk as order_date_sk
from {{ ref('order_items') }} as oi
inner join {{ ref('orders') }} as o
    on oi.order_id = o.order_id
left join {{ ref('dim_customer') }} as c
    on
        o.customer_id = c.customer_id
        and o.order_date >= c.valid_from
        and o.order_date < c.valid_to
left join {{ ref('dim_product') }} as p
    on oi.product_id = p.product_id
left join {{ ref('dim_date') }} as d
    on o.order_date::date = d.full_date
