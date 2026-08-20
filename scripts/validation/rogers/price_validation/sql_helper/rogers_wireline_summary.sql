SELECT
    status,
    row_count
FROM (
    SELECT
        "Match Status (Service ID)" AS status,
        COUNT(*) AS row_count,
        CASE
            WHEN "Match Status (Service ID)" = 'Matched' THEN 1
            WHEN "Match Status (Service ID)" = 'Rate Mismatch' THEN 2
            WHEN "Match Status (Service ID)" = 'Missing from Price Book' THEN 3
            WHEN "Match Status (Service ID)" = 'Missing Service ID from Report' THEN 4
            WHEN "Match Status (Service ID)" = 'Missing Report Rate' THEN 5
            ELSE 98
        END AS sort_order
    FROM reporting.validate_rogers_wireline_prices('2026-07-31')
    GROUP BY "Match Status (Service ID)"

    UNION ALL

    SELECT
        'Total Rows' AS status,
        COUNT(*) AS row_count,
        99 AS sort_order
    FROM reporting.validate_rogers_wireline_prices('2026-07-31')
) s
ORDER BY sort_order;


