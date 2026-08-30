select
    o.order_id,
    cast(o.customer_id as varchar) as customer_id,
    o.order_total,
    o.created_at
from {{ ref('stg_orders') }} as o
cross join {{ source('raw', 'customer_segments') }} as segments
