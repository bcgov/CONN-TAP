-- Drill-down for telus_raw_validate_duplicate_rows_by_sheet_and_month: returns every
-- raw_telus_spend row that is part of a duplicate group (identical on all columns except
-- raw_id, ingestion_run_id, extras) for one sheet_name and statement calendar month.
-- Rows with amount NULL or 0 are excluded from duplicate detection, matching the validator.
-- Uses one window pass over the filtered slice (avoids correlated EXISTS over the full table).

CREATE OR REPLACE FUNCTION telus_raw_get_duplicate_rows (
  p_sheet_name text,
  p_year int,
  p_month int
)
RETURNS SETOF raw_telus_spend
LANGUAGE sql
STABLE
AS $$
  SELECT
    d.raw_id,
    d.ingestion_run_id,
    d.sheet_name,
    d.account_number,
    d.account_description,
    d.service_number,
    d.statement_date,
    d.due_date,
    d.statement_section,
    d.organization,
    d.statement_category,
    d.statement_sub_category,
    d.record_type_description,
    d.amount,
    d.bill_section,
    d.detail_description,
    d.invoice_number,
    d.month,
    d.service_address,
    d.service_description,
    d.source,
    d.source_id,
    d.extras
  FROM (
    SELECT
      t.*,
      COUNT(*) OVER (
        PARTITION BY
          t.sheet_name,
          t.account_number,
          t.account_description,
          t.service_number,
          t.statement_date,
          t.due_date,
          t.statement_section,
          t.organization,
          t.statement_category,
          t.statement_sub_category,
          t.record_type_description,
          t.amount,
          t.bill_section,
          t.detail_description,
          t.invoice_number,
          t.month,
          t.service_address,
          t.service_description,
          t.source,
          t.source_id
      ) AS _dup_row_count
    FROM raw_telus_spend AS t
    WHERE t.sheet_name IS NOT DISTINCT FROM p_sheet_name
      AND t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = make_date(p_year, p_month, 1)
      AND t.amount IS NOT NULL
      AND t.amount <> 0
  ) AS d
  WHERE d._dup_row_count > 1
  ORDER BY d.raw_id;
$$;
