SELECT *
FROM reporting.validate_rogers_cellular_prices()
WHERE match_status_service_id = 'Matched'
  AND abs(difference_billed_amount_minus_monthly_fixed_fee) > 0.005;