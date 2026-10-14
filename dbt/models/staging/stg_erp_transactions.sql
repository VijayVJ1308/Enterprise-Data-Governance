-- Staging model for ERP General Ledger Transactions
WITH source_data AS (
    SELECT * FROM {{ source('bronze', 'erp_transactions') }}
)

SELECT
    TRIM(CAST(txn_id AS VARCHAR)) AS txn_id,
    CAST(amount_usd AS DECIMAL(14,2)) AS amount_usd,
    UPPER(TRIM(CAST(currency AS VARCHAR))) AS currency,
    CAST(timestamp AS TIMESTAMP) AS transaction_timestamp,
    SUBSTRING(CAST(timestamp AS VARCHAR), 1, 7) AS settlement_month,
    CURRENT_TIMESTAMP AS _stg_loaded_at
FROM source_data
WHERE txn_id IS NOT NULL
