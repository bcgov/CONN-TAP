-- Telus raw_data.raw_telus_spend validation (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Returns rows where validation fails. Use p_statement_month := NULL to scan the full table;
-- pass any date within the target month (e.g. date '2026-03-15') to restrict to rows where
-- date_trunc('month', statement_date) matches that month. Rows with NULL statement_date are
-- included only when p_statement_month IS NULL; they return NULL for contradiction_year /
-- contradiction_month.

-- Flags physical columns on raw_data.raw_telus_spend that have at least one NULL or all-whitespace value
-- within each (sheet_name, statement month). Omitted columns (blanks allowed): bill_section,
-- service_address, service_description, detail_description, extras.

CREATE OR REPLACE FUNCTION telus_raw_validate_blanks_by_sheet_and_month (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  contradiction_year int,
  contradiction_month int,
  blank_column text
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
  g AS (
    SELECT
      b.sheet_name,
      MAX(EXTRACT(YEAR FROM b.statement_date))::int AS contradiction_year,
      MAX(EXTRACT(MONTH FROM b.statement_date))::int AS contradiction_month,
      bool_or(b.account_number IS NULL OR trim(both FROM b.account_number) = '')
        AS account_number_blanks,
      bool_or(b.account_description IS NULL OR trim(both FROM b.account_description) = '')
        AS account_description_blanks,
      bool_or(b.service_number IS NULL OR trim(both FROM b.service_number) = '')
        AS service_number_blanks,
      bool_or(b.statement_date IS NULL) AS statement_date_blanks,
      bool_or(b.due_date IS NULL) AS due_date_blanks,
      bool_or(b.statement_section IS NULL OR trim(both FROM b.statement_section) = '')
        AS statement_section_blanks,
      bool_or(b.organization IS NULL OR trim(both FROM b.organization) = '')
        AS organization_blanks,
      bool_or(b.statement_category IS NULL OR trim(both FROM b.statement_category) = '')
        AS statement_category_blanks,
      bool_or(b.statement_sub_category IS NULL OR trim(both FROM b.statement_sub_category) = '')
        AS statement_sub_category_blanks,
      bool_or(
        b.record_type_description IS NULL OR trim(both FROM b.record_type_description) = ''
      ) AS record_type_description_blanks,
      bool_or(b.amount IS NULL) AS amount_blanks,
      bool_or(b.invoice_number IS NULL OR trim(both FROM b.invoice_number) = '')
        AS invoice_number_blanks,
      bool_or(b.month IS NULL OR trim(both FROM b.month) = '') AS month_blanks,
      bool_or(b.source IS NULL OR trim(both FROM b.source) = '') AS source_blanks,
      bool_or(b.source_id IS NULL OR trim(both FROM b.source_id) = '') AS source_id_blanks
    FROM base AS b
    GROUP BY
      b.sheet_name,
      date_trunc('month', b.statement_date)
  )
  SELECT g.sheet_name, g.contradiction_year, g.contradiction_month, v.blank_column
  FROM g
  CROSS JOIN LATERAL (
    VALUES
      ('account_number'::text, g.account_number_blanks),
      ('account_description', g.account_description_blanks),
      ('service_number', g.service_number_blanks),
      ('statement_date', g.statement_date_blanks),
      ('due_date', g.due_date_blanks),
      ('statement_section', g.statement_section_blanks),
      ('organization', g.organization_blanks),
      ('statement_category', g.statement_category_blanks),
      ('statement_sub_category', g.statement_sub_category_blanks),
      ('record_type_description', g.record_type_description_blanks),
      ('amount', g.amount_blanks),
      ('invoice_number', g.invoice_number_blanks),
      ('month', g.month_blanks),
      ('source', g.source_blanks),
      ('source_id', g.source_id_blanks)
  ) AS v (blank_column, has_blank)
  WHERE v.has_blank
  ORDER BY
    g.contradiction_year NULLS LAST,
    g.contradiction_month NULLS LAST,
    g.sheet_name NULLS LAST,
    v.blank_column;
$$;
