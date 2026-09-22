
-- =====================================================================
-- Rogers wireline price validation
-- ---------------------------------------------------------------------
--After running the rogers_wireline_function, you can check the price validation results.
-- the Function contain the condition for report date:
--p_billing_date IS NULL
--OR billing_date = p_billing_date
--when you pass NULL, the function does not filter by billing date and returns results for all billing dates/reports.
-- Call it with a year and a month, e.g.
--reporting.validate_rogers_wireline_prices('2026-07-31')


-- ----------------------------------------------------------------------

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
    FROM reporting.validate_rogers_wireline_prices(NULL)
    GROUP BY "Match Status (Service ID)"

    UNION ALL

    SELECT
        'Total Rows' AS status,
        COUNT(*) AS row_count,
        99 AS sort_order
    FROM reporting.validate_rogers_wireline_prices(NULL)
) s
ORDER BY sort_order;


