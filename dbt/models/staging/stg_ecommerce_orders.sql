-- Staging model for Ecommerce Orders
WITH source_data AS (
    SELECT * FROM {{ source('bronze', 'ecommerce_orders') }}
)

SELECT
    TRIM(CAST(order_id AS VARCHAR)) AS order_id,
    TRIM(CAST(customer_id AS VARCHAR)) AS customer_id,
    CAST(total_amount AS DECIMAL(12,2)) AS total_amount,
    UPPER(TRIM(CAST(status AS VARCHAR))) AS order_status,
    CAST(timestamp AS TIMESTAMP) AS order_timestamp,
    CURRENT_TIMESTAMP AS _stg_loaded_at
FROM source_data
WHERE order_id IS NOT NULL
