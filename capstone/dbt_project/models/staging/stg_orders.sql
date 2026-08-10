with source as (
    select * from {{ source('public', 'raw_orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        product_id,
        order_date,
        quantity,
        status,
        revenue
    from source
)

select * from renamed
