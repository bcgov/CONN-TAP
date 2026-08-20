SELECT *
FROM reporting.validate_rogers_cellular_prices()
WHERE invoice_date = DATE '2025-07-01'
  AND match_status_service_id = 'Missing Service ID from Report';