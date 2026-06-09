SELECT
  s.feed,
  s.rcid_cust_nm,
  EXTRACT(YEAR FROM s.month_start_dt)::int  AS year_num,
  EXTRACT(MONTH FROM s.month_start_dt)::int AS month_num,
  SUM(s.billed_amt) AS total_billed_amt
FROM (
  SELECT 'managed_security'::text AS feed, rcid_cust_nm, month_start_dt, billed_amt
  FROM raw_data.tsma_other_managed_security
  UNION ALL
  SELECT 'managed_router'::text, rcid_cust_nm, month_start_dt, billed_amt
  FROM raw_data.tsma_other_managed_router
  UNION ALL
  SELECT 'managed_wlan_wifi'::text AS feed, rcid_cust_nm, month_start_dt, billed_amt
  FROM raw_data.tsma_wireline
  WHERE LOWER(tsma_service_tower) = 'managed wlan'
) AS s
WHERE s.month_start_dt IS NOT NULL
GROUP BY s.feed, s.rcid_cust_nm,
  EXTRACT(YEAR FROM s.month_start_dt)::int,
  EXTRACT(MONTH FROM s.month_start_dt)::int
ORDER BY s.rcid_cust_nm, s.feed, year_num, month_num;
