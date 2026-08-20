-- =========================================================
-- Rogers Cellular Price Validation
-- Based on updated Python workbook output
--
-- Source tables:
--   raw_data.raw_rogers_spend_cellular
--   raw_data.raw_rogers_cellular_pricebook
--
-- Main function:
--   reporting.validate_rogers_cellular_prices()
--
-- Summary function:
--   reporting.validate_rogers_cellular_summary()
-- =========================================================


-- =========================================================
-- 1. Create reporting schema
-- =========================================================
CREATE SCHEMA IF NOT EXISTS reporting;


-- =========================================================
-- 2. Drop old functions first
-- Needed because PostgreSQL cannot change return table structure
-- using CREATE OR REPLACE FUNCTION
-- =========================================================
DROP FUNCTION IF EXISTS reporting.validate_rogers_cellular_summary();
DROP FUNCTION IF EXISTS reporting.validate_rogers_cellular_prices();
DROP FUNCTION IF EXISTS reporting.normalize_service_id(text);
DROP FUNCTION IF EXISTS reporting.parse_money(text);


-- =========================================================
-- 3. Helper function: normalize service_id
--
-- Python equivalent:
-- CVDULTDM -> CVDULTD
-- If service_id ends with M, remove final M
-- =========================================================
CREATE OR REPLACE FUNCTION reporting.normalize_service_id(p_service_id text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS
$$
    SELECT
        CASE
            WHEN p_service_id IS NULL THEN ''
            WHEN length(btrim(p_service_id)) > 1
                 AND right(btrim(p_service_id), 1) = 'M'
                THEN left(btrim(p_service_id), length(btrim(p_service_id)) - 1)
            ELSE btrim(p_service_id)
        END;
$$;


-- =========================================================
-- 4. Helper function: parse money text to numeric
--
-- Examples:
--   '$7.49 per seat' -> 7.49
--   '$12.00'         -> 12.00
--   'No Charge'      -> 0.00
--   '($10.00)'       -> -10.00
--   '-10.00'         -> -10.00
--   'n/a'            -> NULL
-- =========================================================
CREATE OR REPLACE FUNCTION reporting.parse_money(p_value text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS
$$
DECLARE
    v_text text;
    v_lower text;
    v_clean text;
    v_num_text text;
    v_amount numeric;
    v_parentheses_negative boolean := false;
BEGIN
    IF p_value IS NULL THEN
        RETURN NULL;
    END IF;

    v_text := btrim(p_value);

    IF v_text = '' THEN
        RETURN NULL;
    END IF;

    v_lower := lower(v_text);

    IF v_lower LIKE '%no charge%' THEN
        RETURN 0;
    END IF;

    IF v_lower IN ('n/a', 'na', 'none') THEN
        RETURN NULL;
    END IF;

    -- Check accounting-style negative values like ($12.34)
    IF v_text LIKE '(%' AND v_text LIKE '%)' THEN
        v_parentheses_negative := true;
    END IF;

    -- Clean common money characters
    v_clean := v_text;
    v_clean := replace(v_clean, ',', '');
    v_clean := replace(v_clean, '$', '');
    v_clean := replace(v_clean, '(', '');
    v_clean := replace(v_clean, ')', '');
    v_clean := btrim(v_clean);

    -- Extract first numeric value from text
    -- Works for values like '7.49 per seat'
    v_num_text := substring(v_clean FROM '[-+]?[0-9]+[.]?[0-9]*');

    IF v_num_text IS NULL OR v_num_text = '' THEN
        RETURN NULL;
    END IF;

    v_amount := v_num_text::numeric;

    IF v_parentheses_negative AND v_amount > 0 THEN
        v_amount := -v_amount;
    END IF;

    RETURN v_amount;
END;
$$;


-- =========================================================
-- 5. Main validation function
--
-- Output is equivalent to your Python "Complete comparison"
-- but includes invoice_date so you can filter by billing month.
--
-- Includes:
--   Matched
--   Missing from Price Book
--   Missing Service ID from Report
--   Difference calculation
-- =========================================================
CREATE OR REPLACE FUNCTION reporting.validate_rogers_cellular_prices()
RETURNS TABLE (
    invoice_date date,
    price_book_service_id text,
    monthly_report_service_id text,
    match_status_service_id text,
    monthly_fixed_fee_from_price_book numeric,
    billed_amount_rate numeric,
    msf_other_options numeric,
    hardware numeric,
    others numeric,
    difference_billed_amount_minus_monthly_fixed_fee numeric
)
LANGUAGE sql
AS
$$
WITH price_clean AS (

    SELECT DISTINCT ON (
        reporting.normalize_service_id(p.service_id)
    )
        p.service_id AS price_book_service_id,
        reporting.normalize_service_id(p.service_id) AS normalized_service_id,
        reporting.parse_money(p.monthly_fixed_fee) AS monthly_fixed_fee_numeric
    FROM raw_data.raw_rogers_cellular_pricebook p
    WHERE reporting.normalize_service_id(p.service_id) <> ''
    ORDER BY
        reporting.normalize_service_id(p.service_id),
        p.raw_id

),

report_prepared AS (

    SELECT
        s.invoice_date,
        s.service_id AS monthly_report_service_id,
        reporting.normalize_service_id(s.service_id) AS normalized_service_id,
        s.billed_amount_pre_tax AS billed_amount_rate,
        s.msf_other_options,
        s.hardware,
        s.others
    FROM raw_data.raw_rogers_spend_cellular s

),

report_nonzero AS (

    SELECT *
    FROM report_prepared
    WHERE billed_amount_rate IS DISTINCT FROM 0

),

report_for_comparison AS (

    SELECT *
    FROM report_nonzero
    WHERE monthly_report_service_id IS NOT NULL
      AND btrim(monthly_report_service_id) <> ''

),

comparison AS (

    SELECT
        r.invoice_date,
        p.price_book_service_id,
        r.monthly_report_service_id,

        CASE
            WHEN p.price_book_service_id IS NOT NULL
                THEN 'Matched'
            ELSE 'Missing from Price Book'
        END AS match_status_service_id,

        p.monthly_fixed_fee_numeric AS monthly_fixed_fee_from_price_book,
        r.billed_amount_rate,
        r.msf_other_options,
        r.hardware,
        r.others,

        CASE
            WHEN p.monthly_fixed_fee_numeric IS NULL
              OR r.billed_amount_rate IS NULL
                THEN NULL
            ELSE r.billed_amount_rate - p.monthly_fixed_fee_numeric
        END AS difference_billed_amount_minus_monthly_fixed_fee

    FROM report_for_comparison r
    LEFT JOIN price_clean p
        ON r.normalized_service_id = p.normalized_service_id

),

missing_service_id_from_report AS (

    SELECT
        r.invoice_date,
        NULL::text AS price_book_service_id,
        r.monthly_report_service_id,
        'Missing Service ID from Report'::text AS match_status_service_id,
        NULL::numeric AS monthly_fixed_fee_from_price_book,
        r.billed_amount_rate,
        r.msf_other_options,
        r.hardware,
        r.others,
        NULL::numeric AS difference_billed_amount_minus_monthly_fixed_fee
    FROM report_nonzero r
    WHERE r.monthly_report_service_id IS NULL
       OR btrim(r.monthly_report_service_id) = ''

),

complete_comparison AS (

    SELECT *
    FROM comparison

    UNION ALL

    SELECT *
    FROM missing_service_id_from_report

)

SELECT
    invoice_date,
    price_book_service_id,
    monthly_report_service_id,
    match_status_service_id,
    monthly_fixed_fee_from_price_book,
    billed_amount_rate,
    msf_other_options,
    hardware,
    others,
    difference_billed_amount_minus_monthly_fixed_fee

FROM complete_comparison

ORDER BY
    CASE match_status_service_id
        WHEN 'Missing Service ID from Report' THEN 0
        WHEN 'Matched' THEN 1
        WHEN 'Missing from Price Book' THEN 2
        ELSE 9
    END,
    invoice_date,
    monthly_report_service_id;
$$;


-- =========================================================
-- 6. Summary function
--
-- Equivalent to your Python Summary sheet
-- =========================================================
CREATE OR REPLACE FUNCTION reporting.validate_rogers_cellular_summary()
RETURNS TABLE (
    metric text,
    value bigint
)
LANGUAGE sql
AS
$$
WITH comparison AS (

    SELECT *
    FROM reporting.validate_rogers_cellular_prices()

),

zero_billed AS (

    SELECT count(*) AS cnt
    FROM raw_data.raw_rogers_spend_cellular
    WHERE billed_amount_pre_tax = 0

),

mismatched_rate AS (

    SELECT count(*) AS cnt
    FROM comparison
    WHERE match_status_service_id = 'Matched'
      AND abs(difference_billed_amount_minus_monthly_fixed_fee) > 0.005

)

SELECT
    'Matched Service IDs' AS metric,
    count(*)::bigint AS value
FROM comparison
WHERE match_status_service_id = 'Matched'

UNION ALL

SELECT
    'Missing from Price Book' AS metric,
    count(*)::bigint AS value
FROM comparison
WHERE match_status_service_id = 'Missing from Price Book'

UNION ALL

SELECT
    'Missing Service ID from Report' AS metric,
    count(*)::bigint AS value
FROM comparison
WHERE match_status_service_id = 'Missing Service ID from Report'

UNION ALL

SELECT
    'Mismatched Rate' AS metric,
    cnt::bigint AS value
FROM mismatched_rate

UNION ALL

SELECT
    'Rows removed because billed amount is zero' AS metric,
    cnt::bigint AS value
FROM zero_billed

UNION ALL

SELECT
    'Total comparison rows' AS metric,
    count(*)::bigint AS value
FROM comparison;
$$;
