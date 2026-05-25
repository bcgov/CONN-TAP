-- name: service_category_vendor_spend
WITH filtered AS (
    SELECT
        service_category,
        vendor,
        SUM(spend_amount)::numeric(19, 4) AS spend_amount,
        (SUM(spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
    FROM staging.service_category_vendor_spend
    WHERE (
            :year IS NULL
            OR (:year_type = 'calendar' AND calendar_year = :year)
            OR (:year_type = 'fiscal' AND fiscal_year = :year)
        )
        AND (
            :quarter IS NULL
            OR (:year_type = 'calendar' AND calendar_quarter = :quarter)
            OR (:year_type = 'fiscal' AND fiscal_quarter = :quarter)
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
