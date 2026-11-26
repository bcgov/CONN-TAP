-- name: isp_spend_indicators
-- Row-level security on bge_service_category_spend limits org users to their
-- assigned organizations (dbt macro org_row_security); TO roles see every row.
SELECT
    SUM(s.spend_amount)::numeric(19, 4)                                                     AS total_spend,
    SUM(CASE WHEN p.code = 'telus'  THEN s.spend_amount ELSE 0 END)::numeric(19, 4)         AS telus_spend,
    SUM(CASE WHEN p.code = 'rogers' THEN s.spend_amount ELSE 0 END)::numeric(19, 4)         AS rogers_spend
FROM analytics.bge_service_category_spend s
JOIN reference_data.provider p ON p.id = s.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR to_char(s.period_key, 'YYYY-MM') = ANY(CAST(:period AS text[]))
    )
