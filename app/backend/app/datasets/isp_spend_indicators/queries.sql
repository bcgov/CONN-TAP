-- name: isp_spend_indicators
SELECT
    SUM(spend_amount)::numeric(19, 4)                                              AS total_spend,
    SUM(CASE WHEN vendor = 'telus'  THEN spend_amount ELSE 0 END)::numeric(19, 4)  AS telus_spend,
    SUM(CASE WHEN vendor = 'rogers' THEN spend_amount ELSE 0 END)::numeric(19, 4)  AS rogers_spend
FROM staging.period_vendor_spend
WHERE (
        CAST(:year AS integer) IS NULL
        OR (CAST(:year_type AS text) = 'calendar' AND calendar_year    = CAST(:year AS integer))
        OR (CAST(:year_type AS text) = 'fiscal'   AND fiscal_year      = CAST(:year AS integer))
    )
    AND (
        CAST(:quarter AS integer) IS NULL
        OR (CAST(:year_type AS text) = 'calendar' AND calendar_quarter = CAST(:quarter AS integer))
        OR (CAST(:year_type AS text) = 'fiscal'   AND fiscal_quarter   = CAST(:quarter AS integer))
    )
