select
    created_at as order_date,
    sum(order_total) as revenue
from {{ ref('orders') }}
group by created_at
