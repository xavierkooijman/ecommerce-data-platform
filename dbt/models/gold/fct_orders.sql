select
    {{ dbt_utils.generate_surrogate_key(['o.order_id']) }} as order_sk,
    o.order_id,
    coalesce(c.customer_sk, '-1') as customer_sk,
    o.status,
    o.payment_method,
    o.order_date,
    order_date.date_sk as order_date_sk,
    s.carrier,
    s.shipped_at,
    shipped_at.date_sk as shipped_at_sk,
    s.delivered_at,
    delivered_at.date_sk as delivered_at_sk,
    o.updated_at
from {{ ref('orders') }} as o
left join {{ ref('dim_customer') }} as c
    on
        o.customer_id = c.customer_id
        and o.order_date >= c.valid_from
        and o.order_date < c.valid_to
left join {{ ref('dim_date') }} as order_date
    on o.order_date::date = order_date.full_date
left join {{ ref('shipments') }} as s
    on o.order_id = s.order_id
left join {{ ref('dim_date') }} as shipped_at
    on s.shipped_at::date = shipped_at.full_date
left join {{ ref('dim_date') }} as delivered_at
    on s.delivered_at::date = delivered_at.full_date
