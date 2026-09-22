-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- Coercibility of values to intended semantic types (see mapping below). Only checks that can
-- fail on raw_data.raw_telus_spend as ingested: text columns that must be numeric strings, and month.
-- month validity matches get_month_non_date_telus: YYYY-MM[-DD], leading month-name prefix,
-- MM[/\-]YYYY, or YYYY-MM-DD HH:MM:SS; NULL / non-matching values are flagged.
-- account_description, service_number, statement_section, organization, statement_category,
-- statement_sub_category, bill_section, detail_description, service_address, service_description,
-- source → text (always valid in Postgres text). statement_date, due_date, amount → native
-- date / numeric in schema (no extra parse check). Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_column_value_types (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  contradiction_year int,
  contradiction_month int,
  failed_column text,
  contradiction_row_count bigint
)
LANGUAGE sql
STABLE
AS $$
  WITH base AS (
    SELECT *
    FROM raw_data.raw_telus_spend AS t
    WHERE (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  ),
  flagged AS (
    SELECT
      b.sheet_name,
      EXTRACT(YEAR FROM b.statement_date)::int AS contradiction_year,
      EXTRACT(MONTH FROM b.statement_date)::int AS contradiction_month,
      v.failed_column,
      COUNT(*)::bigint AS contradiction_row_count
    FROM base AS b
    CROSS JOIN LATERAL (
      SELECT 'account_number'::text AS failed_column
      WHERE
        b.account_number IS NOT NULL
        AND trim(both FROM b.account_number) <> ''
        AND trim(both FROM replace(b.account_number, ',', ''))
          !~ '^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$'

      UNION ALL

      SELECT 'invoice_number'::text
      WHERE
        b.invoice_number IS NOT NULL
        AND trim(both FROM b.invoice_number) <> ''
        AND trim(both FROM replace(b.invoice_number, ',', ''))
          !~ '^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$'

      UNION ALL

      SELECT 'source_id'::text
      WHERE
        b.source_id IS NOT NULL
        AND trim(both FROM b.source_id) <> ''
        AND trim(both FROM replace(b.source_id, ',', ''))
          !~ '^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$'

      UNION ALL

      SELECT 'month'::text
      WHERE
        b.month IS NULL
        OR NOT (
            trim(both FROM b.month) ~ '^\d{4}-\d{2}(-\d{2})?$'
         OR trim(both FROM b.month)
          ~* '^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
         OR trim(both FROM b.month) ~ '^\d{1,2}[\/\-]\d{4}$'
         OR trim(both FROM b.month)
          ~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        )
    ) AS v
    GROUP BY
      b.sheet_name,
      EXTRACT(YEAR FROM b.statement_date)::int,
      EXTRACT(MONTH FROM b.statement_date)::int,
      v.failed_column
  )
  SELECT
    f.sheet_name,
    f.contradiction_year,
    f.contradiction_month,
    f.failed_column,
    f.contradiction_row_count
  FROM flagged AS f
  ORDER BY
    f.contradiction_year NULLS LAST,
    f.contradiction_month NULLS LAST,
    f.sheet_name NULLS LAST,
    f.failed_column;
$$;
