-- name: monthly
-- Row-level security on bge_service_category_spend limits org users to their
-- assigned organizations (dbt macro org_row_security); TO roles see every row.
SELECT
    period_key,
    SUM(spend_amount)::numeric(19, 4)                AS total_spend,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6)  AS total_spend_millions
FROM analytics.bge_service_category_spend
GROUP BY period_key
ORDER BY period_key
