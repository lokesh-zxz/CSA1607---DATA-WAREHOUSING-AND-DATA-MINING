with source as (
    select * from {{ source('public', 'raw_customers') }}
),

renamed as (
    select
        customer_id,
        name as customer_name,
        email,
        signup_date,
        segment,
        country
    from source
)

select * from renamed
