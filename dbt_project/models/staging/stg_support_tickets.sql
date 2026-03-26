{{ config(materialized='view') }}

-- Tickets are joined with restaurant context in restaurant_support.
with source as (
    select * from {{ source('silver', 'restaurant_support') }}
),

deduped as (
    select
        ticket_id,
        order_id,
        restaurant_id,
        order_city      as city,
        cuisine_type,
        ticket_type,
        created_ts,
        resolution_status,
        _ingested_at,
        row_number() over (partition by ticket_id order by _ingested_at desc) as rn
    from source
    where ticket_id is not null
)

select ticket_id, order_id, restaurant_id, city, cuisine_type,
       ticket_type, created_ts, resolution_status, _ingested_at
from deduped
where rn = 1
