-- Fact Transactions Model
WITH stg_transactions AS (
    SELECT * FROM {{ ref('stg_erp_transactions') }}
)

SELECT
    txn_id,
    amount_usd,
    currency,
    transaction_timestamp,
    settlement_month,
    CASE 
        WHEN amount_usd < 0 THEN 'REFUND'
        WHEN amount_usd = 0 THEN 'ZERO_BALANCE'
        ELSE 'SETTLEMENT'
    END AS transaction_category,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM stg_transactions
