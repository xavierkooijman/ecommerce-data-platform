with dates as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2000-01-01' as date)",
        end_date="cast('2100-01-01' as date)"
    ) }}
)

select
    to_char(date_day, 'YYYYMMDD')::integer as date_sk,
    date_day::date as full_date,
    extract(day from date_day)::integer as day_of_month,
    extract(isodow from date_day)::integer as day_of_week,
    extract(month from date_day)::integer as month_number,
    extract(quarter from date_day)::integer as quarter,
    extract(year from date_day)::integer as year,
    extract(isodow from date_day) in (6, 7) as is_weekend
from dates