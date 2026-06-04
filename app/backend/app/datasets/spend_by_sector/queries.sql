-- name: fiscal
SELECT
    sector,
    vendor,
    SUM(spend_amount)::numeric(19, 4)               AS spend_amount,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM staging.sector_vendor_spend
WHERE (
        CAST(:periods AS text) IS NULL
        OR (fiscal_year::text || '_' || fiscal_quarter::text) = ANY(CAST(:periods AS text[]))
    )
GROUP BY sector, vendor
ORDER BY SUM(spend_amount) DESC

-- name: calendar
SELECT
    sector,
    vendor,
    SUM(spend_amount)::numeric(19, 4)               AS spend_amount,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM staging.sector_vendor_spend
WHERE (
        CAST(:periods AS text) IS NULL
        OR (calendar_year::text || '_' || calendar_quarter::text) = ANY(CAST(:periods AS text[]))
    )
GROUP BY sector, vendor
ORDER BY SUM(spend_amount) DESC
