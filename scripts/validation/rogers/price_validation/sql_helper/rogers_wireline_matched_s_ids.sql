SELECT *
FROM reporting.validate_rogers_wireline_prices('2026-07-31')
WHERE "Match Status (Service ID)" = 'Matched'
ORDER BY "Monthly Report Service ID";




