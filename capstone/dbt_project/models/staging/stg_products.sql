with source as (
    select * from {{ source('public', 'raw_products') }}
),

renamed as (
    select
        product_id,
        product_name,
        category,
        cost
    from source
)

select * from renamed
