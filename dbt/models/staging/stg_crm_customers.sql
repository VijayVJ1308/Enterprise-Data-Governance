-- Staging model for CRM Customers
WITH source_data AS (
    SELECT * FROM {{ source('bronze', 'crm_customers') }}
)

SELECT
    TRIM(CAST(customer_id AS VARCHAR)) AS customer_id,
    TRIM(CAST(first_name AS VARCHAR)) AS first_name,
    LOWER(TRIM(CAST(email AS VARCHAR))) AS email,
    COALESCE(TRIM(CAST(domain AS VARCHAR)), 'CRM') AS domain,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CURRENT_TIMESTAMP AS _stg_loaded_at
FROM source_data
WHERE customer_id IS NOT NULL
