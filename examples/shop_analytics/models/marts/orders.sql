select
    o.order_id,
    o.customer_id,
    o.order_total,
    o.created_at
from {{ ref('stg_orders') }} as o
where o.created_at >= current_date - interval '7 days'
