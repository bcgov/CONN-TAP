-- name: received_months
-- One row per report and month that has data. Not organization data, so every
-- role sees every row (no row-level security on this table).
SELECT
    report_name,
    period_key
FROM analytics.report_period_received
