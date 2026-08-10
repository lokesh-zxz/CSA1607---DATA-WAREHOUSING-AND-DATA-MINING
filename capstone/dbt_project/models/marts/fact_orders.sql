with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

products as (
    select * from {{ ref('stg_products') }}
)

select
    o.order_id,
    o.customer_id,
    o.product_id,
    o.order_date,
    o.quantity,
    o.status,
    o.revenue,
    p.cost,
    (o.revenue - p.cost) as profit
from orders o
left join customers c on o.customer_id = c.customer_id
left join products p on o.product_id = p.product_id
