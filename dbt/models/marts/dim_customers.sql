-- Dimension Customer Model
WITH stg_customers AS (
    SELECT * FROM {{ ref('stg_crm_customers') }}
)

SELECT
    customer_id,
    first_name,
    email,
    domain,
    created_at AS customer_since,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM stg_customers
