SELECT *
FROM reporting.validate_rogers_wireline_prices('2025-07-31')
WHERE "Match Status (Service ID)" = 'Rate Mismatch'
ORDER BY
    ABS("Difference (Rate - Monthly Fixed Fee)") DESC,
    "Monthly Report Service ID";




