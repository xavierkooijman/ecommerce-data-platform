select
    {{ dbt_utils.generate_surrogate_key(['id']) }} as product_sk,
    product_sk,
    id,
    sku,
    product_name,
    category,
    price,
    created_at,
    updated_at
from {{ ref('products') }}