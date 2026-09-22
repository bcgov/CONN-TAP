-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- Same duplicate detection as telus_raw_validate_duplicate_rows_by_sheet_and_month (same category
-- exclusions apply), plus duplicate_amount_sum (sum of amount over every row in duplicate groups).
-- Sorted by sheet_name for easier visual review, then statement month.

CREATE OR REPLACE FUNCTION telus_raw_summarize_duplicate_rows_by_sheet_and_month (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  contradiction_year int,
  contradiction_month int,
  duplicate_group_count bigint,
  duplicate_row_count bigint,
  duplicate_amount_sum numeric
)
LANGUAGE sql
STABLE
AS $$
  WITH base AS (
    SELECT *
    FROM raw_data.raw_telus_spend AS t
    WHERE t.amount IS NOT NULL
      AND t.amount <> 0
      AND lower(trim(both FROM COALESCE(t.statement_category, ''))) NOT IN (
        'payment', 'payments', 'amount due from last bill', 'taxes'
      )
      AND (
        p_statement_month IS NULL
        OR (
          t.statement_date IS NOT NULL
          AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
        )
      )
  ),
  dup_with_month AS (
    SELECT
      t.sheet_name,
      date_trunc('month', t.statement_date) AS stmt_month,
      COUNT(*)::bigint AS cnt,
      SUM(t.amount) AS grp_amount_sum
    FROM base AS t
    GROUP BY
      t.sheet_name,
      date_trunc('month', t.statement_date),
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
    HAVING COUNT(*) > 1
  )
  SELECT
    d.sheet_name,
    EXTRACT(YEAR FROM d.stmt_month)::int AS contradiction_year,
    EXTRACT(MONTH FROM d.stmt_month)::int AS contradiction_month,
    COUNT(*)::bigint AS duplicate_group_count,
    SUM(d.cnt)::bigint AS duplicate_row_count,
    SUM(d.grp_amount_sum)::numeric AS duplicate_amount_sum
  FROM dup_with_month AS d
  GROUP BY
    d.sheet_name,
    d.stmt_month
  ORDER BY
    d.sheet_name NULLS LAST,
    d.stmt_month NULLS LAST;
$$;
