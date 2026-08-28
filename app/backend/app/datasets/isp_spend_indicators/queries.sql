-- name: isp_spend_indicators
SELECT
    SUM(pvs.spend_amount)::numeric(19, 4)                                                   AS total_spend,
    SUM(CASE WHEN p.code = 'telus'  THEN pvs.spend_amount ELSE 0 END)::numeric(19, 4)       AS telus_spend,
    SUM(CASE WHEN p.code = 'rogers' THEN pvs.spend_amount ELSE 0 END)::numeric(19, 4)       AS rogers_spend
FROM analytics.period_vendor_spend pvs
JOIN reference_data.provider p ON p.id = pvs.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR to_char(pvs.period_key, 'YYYY-MM') = ANY(CAST(:period AS text[]))
    )
