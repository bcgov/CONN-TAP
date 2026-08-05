-- name: service_category_vendor_spend
WITH filtered AS (
    SELECT
        sc.name                                             AS service_category,
        sc.code                                             AS service_category_code,
        p.code                                              AS vendor,
        SUM(scvs.spend_amount)::numeric(19, 4)             AS spend_amount,
        (SUM(scvs.spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
    FROM analytics.service_category_vendor_spend scvs
    JOIN reference_data.service_category sc ON sc.id = scvs.service_category_id
    JOIN reference_data.provider p ON p.id = scvs.provider_id
    WHERE (
            CAST(:period AS text) IS NULL
            OR (CAST(:year_type AS text) = 'calendar' AND (calendar_year::text || '_' || calendar_quarter::text) = ANY(CAST(:period AS text[])))
            OR (CAST(:year_type AS text) = 'fiscal' AND (fiscal_year::text || '_' || fiscal_quarter::text) = ANY(CAST(:period AS text[])))
        )
    GROUP BY sc.name, sc.code, p.code
),
ranked AS (
    SELECT
        service_category,
        service_category_code,
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
-- Unknown is unattributed spend, not a service, so it's pinned to the end rather
-- than competing for position by size (false sorts before true). The chart takes
-- its bar order from this row order.
ORDER BY (service_category_code = 'unknown'), total_spend_millions DESC, service_category, vendor
