{{ config(materialized='view') }}

-- Refund data is joined into order_facts at the Silver layer.
-- This view surfaces only orders that had a refund.
with source as (
    select * from {{ source('silver', 'order_facts') }}
)

select
    order_id,
    order_date,
    refund_reason,
    refund_amount,
    _ingested_at
from source
where has_refund = true
