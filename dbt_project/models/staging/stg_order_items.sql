{{ config(materialized='view') }}

-- Aggregated item metrics are embedded in order_facts (item_count, items_subtotal).
-- This view exposes those aggregates at the order grain for downstream marts.
with source as (
    select * from {{ source('silver', 'order_facts') }}
)

select
    order_id,
    item_count,
    items_subtotal,
    _ingested_at
from source
where item_count > 0
