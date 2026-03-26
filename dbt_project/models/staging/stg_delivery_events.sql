{{ config(materialized='view') }}

-- delivery_ops = delivery_events already joined with riders at the Silver layer.
with source as (
    select * from {{ source('silver', 'delivery_ops') }}
),

staged as (
    select
        order_id,
        rider_id,
        rider_city,
        rider_shift,
        event_type,
        event_ts,
        latitude,
        longitude,
        _dq_orphan_order,
        _ingested_at
    from source
    where _dq_orphan_order = false
)

select * from staged
