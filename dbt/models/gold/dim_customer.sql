with customers as (
    select
        {{ 
            dbt_utils.generate_surrogate_key(['customer_id', 'dbt_valid_from']) 
        }}
            as customer_sk,
        customer_id,
        email,
        first_name,
        last_name,
        country,
        city,
        is_active,
        signup_date,
        dbt_valid_to is null as is_current,
        dbt_valid_from as valid_from,
        coalesce(dbt_valid_to, '9999-12-31'::timestamptz) as valid_to
    from {{ ref('customers_snapshot') }}
),

unknown_customer as (
    select
        '-1'::text as customer_sk,
        -1::int as customer_id,
        'unknown'::text as email,
        'unknown'::text as first_name,
        'unknown'::text as last_name,
        'unknown'::text as country,
        null::text as city,
        false as is_active,
        '1900-01-01'::date as signup_date,
        true as is_current,
        '1900-01-01'::timestamptz as valid_from,
        '9999-12-31'::timestamptz as valid_to
)

select *
from customers
union all
select *
from unknown_customer
