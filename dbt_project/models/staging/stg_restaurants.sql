{{ config(materialized='view') }}

-- Restaurant dimension is embedded in restaurant_support. Extract distinct restaurants.
with source as (
    select * from {{ source('silver', 'restaurant_support') }}
),

deduped as (
    select
        restaurant_id,
        order_city       as city,
        cuisine_type,
        rating_band,
        onboarding_date,
        _ingested_at,
        row_number() over (partition by restaurant_id order by _ingested_at desc) as rn
    from source
    where restaurant_id is not null
)

select restaurant_id, city, cuisine_type, rating_band, onboarding_date, _ingested_at
from deduped
where rn = 1
