-- name: fiscal
SELECT
    sector,
    vendor,
    SUM(spend_amount)::numeric(19, 4)               AS spend_amount,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM staging.sector_vendor_spend
WHERE (
        CAST(:years AS text) IS NULL
        OR fiscal_year = ANY(CAST(:years AS integer[]))
    )
    AND (
        CAST(:quarters AS text) IS NULL
        OR fiscal_quarter = ANY(CAST(:quarters AS integer[]))
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
        CAST(:years AS text) IS NULL
        OR calendar_year = ANY(CAST(:years AS integer[]))
    )
    AND (
        CAST(:quarters AS text) IS NULL
        OR calendar_quarter = ANY(CAST(:quarters AS integer[]))
    )
GROUP BY sector, vendor
ORDER BY SUM(spend_amount) DESC
