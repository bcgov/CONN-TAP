-- name: fiscal
SELECT
    svs.sector,
    p.code                                          AS vendor,
    SUM(svs.spend_amount)::numeric(19, 4)           AS spend_amount,
    (SUM(svs.spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM staging.sector_vendor_spend svs
JOIN reference_data.provider p ON p.id = svs.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR (fiscal_year::text || '_' || fiscal_quarter::text) = ANY(CAST(:period AS text[]))
    )
GROUP BY svs.sector, p.code
ORDER BY SUM(svs.spend_amount) DESC

-- name: calendar
SELECT
    svs.sector,
    p.code                                          AS vendor,
    SUM(svs.spend_amount)::numeric(19, 4)           AS spend_amount,
    (SUM(svs.spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM staging.sector_vendor_spend svs
JOIN reference_data.provider p ON p.id = svs.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR (calendar_year::text || '_' || calendar_quarter::text) = ANY(CAST(:period AS text[]))
    )
GROUP BY svs.sector, p.code
ORDER BY SUM(svs.spend_amount) DESC
