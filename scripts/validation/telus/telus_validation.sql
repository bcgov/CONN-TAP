-- Telus raw_telus_spend validation helpers (see local_dev/ngta_postgres_ingest/schema.sql).
--
-- Each routine returns rows where validation fails. Use p_statement_month := NULL to scan
-- the full table; pass any date within the target month (e.g. date '2026-03-15') to restrict
-- to rows where date_trunc('month', statement_date) matches that month.
--
-- Rows with NULL statement_date are included only when p_statement_month IS NULL; they
-- return NULL for contradiction_year / contradiction_month.

CREATE OR REPLACE FUNCTION telus_raw_validate_unlisted_tax_like_detail_descriptions (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  detail_description text
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT
    t.sheet_name,
    t.statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.detail_description) AS detail_description
  FROM raw_telus_spend AS t
  WHERE trim(both FROM COALESCE(t.statement_category, '')) <> 'Taxes'
    AND t.detail_description IS NOT NULL
    AND trim(both FROM t.detail_description) <> ''
    AND (
            trim(both FROM t.detail_description) ILIKE '%gst%'
         OR trim(both FROM t.detail_description) ILIKE '%pst%'
         OR trim(both FROM t.detail_description) ILIKE '%hst%'
         OR trim(both FROM t.detail_description) ILIKE '%qst%'
        )
    AND trim(both FROM t.detail_description) NOT IN (
      'B.C. PST Adjustment',
      'CPS GST 100652692',
      'CPS PST BRITISH COLUMBIA 7%',
      'FP GST Credit',
      'FP PST Credit',
      'GST adj',
      'GST Tax Adjustment',
      'IP TRUNKING PSTN CONNECTION*',
      'IP TRUNKING PSTN CONNECTION 3Y-BC*',
      'NGSTAT5IP STATIC IP 5IP',
      'PRI STARTER BUNDLE ADD''L PSTN LINK*',
      'PST-BC adj'
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name,
    statement_category,
    detail_description;
$$;

-- detail_description values that look device/hardware/equipment/Easy Payment related must match
-- a known allowlist (after trim). Heuristic: hardware, equipment (incl. typo equipement), easy pay /
-- easypay, or device (case-insensitive). Only rows whose source is NULL/blank or Wireless.
-- Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_unlisted_device_related_detail_descriptions (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  source text,
  contradiction_year int,
  contradiction_month int,
  detail_description text,
  contradiction_row_count bigint,
  contradiction_amount_sum numeric
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    t.sheet_name,
    t.statement_category,
    NULLIF(trim(both FROM t.source), '') AS source,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.detail_description) AS detail_description,
    COUNT(*)::bigint AS contradiction_row_count,
    SUM(t.amount) AS contradiction_amount_sum
  FROM raw_telus_spend AS t
  WHERE (
      t.source IS NULL
      OR trim(both FROM t.source) = ''
      OR trim(both FROM t.source) = 'Wireless'
    )
    AND t.detail_description IS NOT NULL
    AND trim(both FROM t.detail_description) <> ''
    AND (
            trim(both FROM t.detail_description) ILIKE '%hardware%'
         OR trim(both FROM t.detail_description) ILIKE '%equipment%'
         OR trim(both FROM t.detail_description) ILIKE '%equipement%'
         OR trim(both FROM t.detail_description) ILIKE '%easypay%'
         OR trim(both FROM t.detail_description) ILIKE '%easy%pay%'
         OR trim(both FROM t.detail_description) ILIKE '%device%'
        )
    AND trim(both FROM t.detail_description) NOT IN (
      'Hardware Purchase Charge',
      'Device Discount Repayment',
      'Monthly TELUS Easy Payment',
      'Device discount repay. canc.',
      'Device discount repay. - CR',
      'Monthly Easy Payment',
      'TELUS Easy Payment Balance',
      'Equipment Adjustment'
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  GROUP BY
    t.sheet_name,
    t.statement_category,
    NULLIF(trim(both FROM t.source), ''),
    EXTRACT(YEAR FROM t.statement_date)::int,
    EXTRACT(MONTH FROM t.statement_date)::int,
    trim(both FROM t.detail_description)
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name NULLS LAST,
    statement_category NULLS LAST,
    source NULLS FIRST,
    detail_description;
$$;

-- Expected: source_id 164 or 130 → source 'Wireless'; source_id 1001, 103, 104, 102, or 106
-- → source 'Wireline'. Any other source_id or any source other than those two is flagged.

CREATE OR REPLACE FUNCTION telus_raw_validate_source_id_matches_expected_source (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  source_id text,
  source text
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT
    t.sheet_name,
    t.statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    trim(both FROM t.source_id) AS source_id,
    trim(both FROM t.source) AS source
  FROM raw_telus_spend AS t
  WHERE NOT (
      (
        trim(both FROM COALESCE(t.source, '')) = 'Wireless'
        AND trim(both FROM COALESCE(t.source_id, '')) IN ('164', '130')
      )
      OR (
        trim(both FROM COALESCE(t.source, '')) = 'Wireline'
        AND trim(both FROM COALESCE(t.source_id, '')) IN ('1001', '103', '104', '102', '106')
      )
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name,
    statement_category,
    source_id,
    source;
$$;

-- Flags physical columns on raw_telus_spend that have at least one NULL or all-whitespace value
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
    FROM raw_telus_spend AS t
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

-- Requires p_statement_month (one month only). Pass any date in that month (e.g. date '2026-03-15').
-- Fails when no sheet_name (for rows in that month) contains one of the expected BGE tokens.
-- MOE and ECC are one requirement: if either appears in any sheet name, both pass; otherwise
-- missing_bge is reported once as 'MOE or ECC'.
-- Most tokens use case-insensitive substring match; SD uses a token-style match (not surrounded
-- by letters/digits) so it does not match inside longer words (e.g. USED).

CREATE OR REPLACE FUNCTION telus_raw_validate_all_bges_in_sheets (
  p_statement_month date
)
RETURNS TABLE (
  contradiction_year int,
  contradiction_month int,
  missing_bge text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  IF p_statement_month IS NULL THEN
    RAISE EXCEPTION 'telus_raw_validate_all_bges_in_sheets: p_statement_month is required';
  END IF;

  RETURN QUERY
  WITH base AS (
    SELECT DISTINCT trim(both FROM t.sheet_name) AS sheet_name
    FROM raw_telus_spend AS t
    WHERE t.statement_date IS NOT NULL
      AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
  ),
  required AS (
    SELECT
      u.bge,
      u.ord
    FROM unnest(
      ARRAY[
        'BCH'::text,
        'BCLC',
        'FHA',
        'FNHA',
        'GBC',
        'ICBC',
        'IHA',
        'NHA',
        'PHSA',
        'SD',
        'VCHA',
        'VIHA',
        'WSBC',
        'BCA'
      ]
    ) WITH ORDINALITY AS u (bge, ord)
  ),
  missing_rows AS (
    SELECT
      EXTRACT(YEAR FROM date_trunc('month', p_statement_month))::int AS contradiction_year,
      EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int AS contradiction_month,
      r.bge AS missing_bge,
      r.ord AS sort_ord
    FROM required AS r
    WHERE NOT EXISTS (
      SELECT 1
      FROM base AS b
      WHERE b.sheet_name IS NOT NULL
        AND b.sheet_name <> ''
        AND (
          r.bge = 'SD'
          AND b.sheet_name ~* '(^|[^[:alnum:]])SD($|[^[:alnum:]])'
          OR r.bge <> 'SD'
          AND b.sheet_name ILIKE '%' || r.bge || '%'
        )
    )

    UNION ALL

    SELECT
      EXTRACT(YEAR FROM date_trunc('month', p_statement_month))::int,
      EXTRACT(MONTH FROM date_trunc('month', p_statement_month))::int,
      'MOE or ECC'::text,
      8
    WHERE NOT EXISTS (
      SELECT 1
      FROM base AS b
      WHERE b.sheet_name IS NOT NULL
        AND b.sheet_name <> ''
        AND (
          b.sheet_name ILIKE '%ECC%'
          OR b.sheet_name ILIKE '%MOE%'
        )
    )
  )
  SELECT
    m.contradiction_year,
    m.contradiction_month,
    m.missing_bge
  FROM missing_rows AS m
  ORDER BY m.sort_ord, m.missing_bge;
END;
$$;

-- statement_category must be one of the known Telus categories below (after trim). Any other
-- value, NULL, or all-whitespace is flagged. Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_statement_category_allowlist (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  statement_category text,
  contradiction_year int,
  contradiction_month int,
  contradiction_row_count bigint
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    t.sheet_name,
    trim(both FROM t.statement_category) AS statement_category,
    EXTRACT(YEAR FROM t.statement_date)::int AS contradiction_year,
    EXTRACT(MONTH FROM t.statement_date)::int AS contradiction_month,
    COUNT(*)::bigint AS contradiction_row_count
  FROM raw_telus_spend AS t
  WHERE (
      t.statement_category IS NULL
      OR trim(both FROM t.statement_category) = ''
      OR trim(both FROM t.statement_category) NOT IN (
        'Adjustment',
        'Adjustments',
        'Alternate Services',
        'Amount due from last bill',
        'Amount Due from last bill',
        'Directory Advertising',
        'Other Charges and Credits',
        'Payment',
        'Payments',
        'Recurring Service Charges',
        'Taxes',
        'Usage'
      )
    )
    AND (
      p_statement_month IS NULL
      OR (
        t.statement_date IS NOT NULL
        AND date_trunc('month', t.statement_date) = date_trunc('month', p_statement_month)
      )
    )
  GROUP BY
    t.sheet_name,
    trim(both FROM t.statement_category),
    EXTRACT(YEAR FROM t.statement_date)::int,
    EXTRACT(MONTH FROM t.statement_date)::int
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name NULLS LAST,
    statement_category NULLS LAST;
$$;

-- Coercibility of values to intended semantic types (see mapping below). Only checks that can
-- fail on raw_telus_spend as ingested: text columns that must be numeric strings, and month.
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
    FROM raw_telus_spend AS t
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

-- Rows that match on every column except raw_id, ingestion_run_id, and extras, within the same
-- sheet_name and calendar month of statement_date, are duplicates. Rows with amount NULL or 0
-- are excluded before duplicate detection. Returns one row per sheet_name + month with how many
-- distinct duplicate signatures exist and total row count in those groups (all copies).
-- Optional month filter like other telus validators.

CREATE OR REPLACE FUNCTION telus_raw_validate_duplicate_rows_by_sheet_and_month (
  p_statement_month date DEFAULT NULL
)
RETURNS TABLE (
  sheet_name text,
  contradiction_year int,
  contradiction_month int,
  duplicate_group_count bigint,
  duplicate_row_count bigint
)
LANGUAGE sql
STABLE
AS $$
  WITH base AS (
    SELECT *
    FROM raw_telus_spend AS t
    WHERE t.amount IS NOT NULL
      AND t.amount <> 0
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
      COUNT(*)::bigint AS cnt
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
    SUM(d.cnt)::bigint AS duplicate_row_count
  FROM dup_with_month AS d
  GROUP BY
    d.sheet_name,
    d.stmt_month
  ORDER BY
    contradiction_year NULLS LAST,
    contradiction_month NULLS LAST,
    sheet_name NULLS LAST;
$$;

-- Same duplicate detection as telus_raw_validate_duplicate_rows_by_sheet_and_month, plus
-- duplicate_amount_sum (sum of amount over every row in duplicate groups). Sorted by sheet_name
-- for easier visual review, then statement month.

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
    FROM raw_telus_spend AS t
    WHERE t.amount IS NOT NULL
      AND t.amount <> 0
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
