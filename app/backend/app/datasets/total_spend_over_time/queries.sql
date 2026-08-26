-- name: monthly
SELECT
    period_key,
    SUM(spend_amount)::numeric(19, 4)                AS total_spend,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6)  AS total_spend_millions
FROM analytics.service_category_vendor_spend
GROUP BY period_key
ORDER BY period_key
