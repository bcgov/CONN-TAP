SELECT *
FROM reporting.validate_rogers_wireline_prices('2025-07-31')
WHERE "Match Status (Service ID)" = 'Missing from Price Book'
ORDER BY "Monthly Report Service ID";



