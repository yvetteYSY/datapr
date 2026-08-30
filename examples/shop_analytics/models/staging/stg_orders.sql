select
    cast(order_id as bigint) as order_id,
    cast(customer_id as bigint) as customer_id,
    cast(order_total as decimal(18, 2)) as order_total,
    cast(created_at as date) as created_at
from {{ source('raw', 'orders') }}
