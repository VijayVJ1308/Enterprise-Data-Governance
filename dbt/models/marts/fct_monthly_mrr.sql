-- Monthly Recurring Revenue (MRR) Mart
WITH transactions AS (
    SELECT * FROM {{ ref('fct_transactions') }}
)

SELECT
    settlement_month,
    currency,
    COUNT(txn_id) AS total_transactions,
    SUM(CASE WHEN amount_usd > 0 THEN amount_usd ELSE 0 END) AS gross_revenue_usd,
    SUM(CASE WHEN amount_usd < 0 THEN ABS(amount_usd) ELSE 0 END) AS refunds_usd,
    SUM(amount_usd) AS net_revenue_usd,
    AVG(amount_usd) AS avg_transaction_usd,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM transactions
GROUP BY settlement_month, currency
