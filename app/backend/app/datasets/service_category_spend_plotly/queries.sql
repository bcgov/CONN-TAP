-- name: service_category_vendor_spend
WITH filtered AS (
    SELECT
        service_category,
        vendor,
        SUM(spend_amount)::numeric(19, 4) AS spend_amount,
        (SUM(spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
    FROM staging.service_category_vendor_spend
    WHERE (
            CAST(:period AS text) IS NULL
            OR (CAST(:year_type AS text) = 'calendar' AND (calendar_year::text || '_' || calendar_quarter::text) = ANY(CAST(:period AS text[])))
            OR (CAST(:year_type AS text) = 'fiscal' AND (fiscal_year::text || '_' || fiscal_quarter::text) = ANY(CAST(:period AS text[])))
        )
    GROUP BY service_category, vendor
),
ranked AS (
    SELECT
        service_category,
        vendor,
        spend_amount,
        spend_millions,
        SUM(spend_millions) OVER (PARTITION BY service_category) AS total_spend_millions
    FROM filtered
)
SELECT
    service_category,
    vendor,
    spend_amount,
    spend_millions,
    total_spend_millions
FROM ranked
ORDER BY total_spend_millions DESC, service_category, vendor
