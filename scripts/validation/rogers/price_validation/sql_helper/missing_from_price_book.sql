SELECT *
FROM reporting.validate_rogers_cellular_prices()
WHERE invoice_date = DATE '2026-06-01'
  AND match_status_service_id = 'Missing from Price Book';