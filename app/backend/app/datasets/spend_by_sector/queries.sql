-- name: spend
SELECT
    s.name                                          AS sector,
    p.code                                          AS vendor,
    SUM(bvs.spend_amount)::numeric(19, 4)           AS spend_amount,
    (SUM(bvs.spend_amount) / 1000000.0)::numeric(19, 6) AS spend_millions
FROM analytics.bge_vendor_spend bvs
JOIN reference_data.bge bg ON bg.id = bvs.bge_id
JOIN reference_data.sector s ON s.id = bg.sector_id
JOIN reference_data.provider p ON p.id = bvs.provider_id
WHERE (
        CAST(:period AS text) IS NULL
        OR to_char(bvs.period_key, 'YYYY-MM') = ANY(CAST(:period AS text[]))
    )
GROUP BY s.name, p.code
ORDER BY SUM(bvs.spend_amount) DESC
