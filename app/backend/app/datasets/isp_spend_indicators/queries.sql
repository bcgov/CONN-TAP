-- name: isp_spend_indicators
SELECT
    SUM(spend_amount)::numeric(19, 4)                                              AS total_spend,
    SUM(CASE WHEN vendor = 'telus'  THEN spend_amount ELSE 0 END)::numeric(19, 4)  AS telus_spend,
    SUM(CASE WHEN vendor = 'rogers' THEN spend_amount ELSE 0 END)::numeric(19, 4)  AS rogers_spend
FROM staging.service_category_vendor_spend
WHERE (
        CAST(:years AS text) IS NULL
        OR (CAST(:year_type AS text) = 'calendar' AND calendar_year   = ANY(CAST(:years AS integer[])))
        OR (CAST(:year_type AS text) = 'fiscal'   AND fiscal_year     = ANY(CAST(:years AS integer[])))
    )
    AND (
        CAST(:quarters AS text) IS NULL
        OR (CAST(:year_type AS text) = 'calendar' AND calendar_quarter = ANY(CAST(:quarters AS integer[])))
        OR (CAST(:year_type AS text) = 'fiscal'   AND fiscal_quarter   = ANY(CAST(:quarters AS integer[])))
    )
