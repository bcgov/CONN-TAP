-- =====================================================================
-- Rogers wireline price validation
-- ---------------------------------------------------------------------
--After running the rogers_wireline_function, you can check the price validation results.
-- the Function contain the condition for report date:
--p_billing_date IS NULL
--OR billing_date = p_billing_date
--when you pass NULL, the function does not filter by billing date and returns results for all billing dates/reports.
-- Call it with a year and a month, e.g.
--SELECT *
--FROM reporting.validate_rogers_wireline_prices('2025-07-31')
--WHERE "Match Status (Service ID)" = 'Rate Mismatch'
--ORDER BY
--    ABS("Difference (Rate - Monthly Fixed Fee)") DESC,
--    "Monthly Report Service ID";
-- ----------------------------------------------------------------------

SELECT *
FROM reporting.validate_rogers_wireline_prices(NULL)
WHERE "Match Status (Service ID)" = 'Rate Mismatch'
ORDER BY
    ABS("Difference (Rate - Monthly Fixed Fee)") DESC,
    "Monthly Report Service ID";




