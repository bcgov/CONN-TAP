-- name: isp_spend_indicators
SELECT
    SUM(pvs.spend_amount)::numeric(19, 4)                                                   AS total_spend,
    SUM(CASE WHEN p.code = 'telus'  THEN pvs.spend_amount ELSE 0 END)::numeric(19, 4)       AS telus_spend,
    SUM(CASE WHEN p.code = 'rogers' THEN pvs.spend_amount ELSE 0 END)::numeric(19, 4)       AS rogers_spend
FROM staging.period_vendor_spend pvs
JOIN reference_data.provider p ON p.id = pvs.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR (CAST(:year_type AS text) = 'calendar' AND (calendar_year::text || '_' || calendar_quarter::text) = ANY(CAST(:period AS text[])))
        OR (CAST(:year_type AS text) = 'fiscal' AND (fiscal_year::text || '_' || fiscal_quarter::text) = ANY(CAST(:period AS text[])))
    )
