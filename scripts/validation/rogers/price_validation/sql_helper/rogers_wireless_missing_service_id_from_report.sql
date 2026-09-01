SELECT *
FROM reporting.validate_rogers_cellular_prices()
WHERE match_status_service_id = 'Missing Service ID from Report';