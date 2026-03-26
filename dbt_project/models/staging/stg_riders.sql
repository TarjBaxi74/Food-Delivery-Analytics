{{ config(materialized='view') }}

-- Rider dimension is embedded in delivery_ops. Extract distinct riders.
with source as (
    select * from {{ source('silver', 'delivery_ops') }}
),

deduped as (
    select
        rider_id,
        rider_city   as city,
        rider_shift  as shift_type,
        joining_date,
        _ingested_at,
        row_number() over (partition by rider_id order by _ingested_at desc) as rn
    from source
    where rider_id is not null
)

select rider_id, city, shift_type, joining_date, _ingested_at
from deduped
where rn = 1
