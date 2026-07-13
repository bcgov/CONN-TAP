=================tsma_lite_spend=========================


WITH lite AS (
    SELECT
        ccyymm,
        SUM(CASE WHEN LOWER(tsma_service_tower) = 'conferencing'
                 THEN COALESCE(billed_amt, 0) ELSE 0 END) AS conferencing_spend,
        SUM(CASE WHEN LOWER(tsma_service_tower) = 'long distance'
                 THEN COALESCE(billed_amt, 0) ELSE 0 END) AS long_distance_spend,
        SUM(CASE WHEN LOWER(tsma_service_tower) = 'voice'
                 THEN COALESCE(billed_amt, 0) ELSE 0 END) AS voice_spend,
        0::numeric AS cellular_spend
    FROM raw_data.tsma_lite_wireline
    WHERE ccyymm BETWEEN '202401' AND '202612'
      AND LOWER(tsma_service_tower) IN ('conferencing', 'long distance', 'voice')
    GROUP BY ccyymm

    UNION ALL

    SELECT
        ccyymm,
        0::numeric AS conferencing_spend,
        0::numeric AS long_distance_spend,
        0::numeric AS voice_spend,
        SUM(COALESCE(billed_amt, 0)) AS cellular_spend
    FROM raw_data.tsma_lite_wireless
    WHERE ccyymm BETWEEN '202401' AND '202612'
    GROUP BY ccyymm
)

SELECT
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(conferencing_spend) AS conferencing_spend,
    SUM(long_distance_spend) AS long_distance_spend,
    SUM(voice_spend) AS voice_spend,
    SUM(cellular_spend) AS cellular_spend
FROM lite
GROUP BY ccyymm
ORDER BY month_start;
