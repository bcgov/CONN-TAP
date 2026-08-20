CREATE SCHEMA IF NOT EXISTS reporting;

DROP FUNCTION IF EXISTS reporting.validate_rogers_wireline_prices(date);
DROP FUNCTION IF EXISTS reporting.validate_rogers_wireline_prices();

DROP FUNCTION IF EXISTS reporting._norm_key(text);
DROP FUNCTION IF EXISTS reporting._get_col_text(jsonb, text[]);
DROP FUNCTION IF EXISTS reporting._parse_money(text);
DROP FUNCTION IF EXISTS reporting._extract_amount(text);
DROP FUNCTION IF EXISTS reporting._to_numeric_plain(text);
DROP FUNCTION IF EXISTS reporting._parse_billing_date(text);


CREATE OR REPLACE FUNCTION reporting._norm_key(p_text text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT regexp_replace(lower(coalesce(p_text, '')), '[^a-z0-9]', '', 'g');
$$;


CREATE OR REPLACE FUNCTION reporting._get_col_text(
    p_row jsonb,
    p_options text[]
)
RETURNS text
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_option text;
    v_key text;
BEGIN
    /*
      Same idea as your Python find_col():

      1. Exact normalized match:
         SERVICE_ID, Service ID, service-id all become serviceid

      2. If not found, try partial text match
    */

    FOREACH v_option IN ARRAY p_options LOOP
        SELECT e.key
        INTO v_key
        FROM jsonb_each_text(p_row) AS e(key, value)
        WHERE reporting._norm_key(e.key) = reporting._norm_key(v_option)
        LIMIT 1;

        IF v_key IS NOT NULL THEN
            RETURN p_row ->> v_key;
        END IF;
    END LOOP;

    FOREACH v_option IN ARRAY p_options LOOP
        SELECT e.key
        INTO v_key
        FROM jsonb_each_text(p_row) AS e(key, value)
        WHERE lower(e.key) LIKE '%' || lower(v_option) || '%'
        LIMIT 1;

        IF v_key IS NOT NULL THEN
            RETURN p_row ->> v_key;
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION reporting._parse_money(p_text text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_text text;
    v_match text;
BEGIN
    /*
      Mirrors your Python parse_money()
    */

    IF p_text IS NULL THEN
        RETURN NULL;
    END IF;

    v_text := replace(trim(p_text), ',', '');

    v_match := substring(v_text FROM '[+-]?[0-9]+[.]?[0-9]*');

    IF v_match IS NULL OR v_match = '' THEN
        RETURN NULL;
    END IF;

    RETURN v_match::numeric;
END;
$$;


CREATE OR REPLACE FUNCTION reporting._extract_amount(p_text text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_text text;
BEGIN
    /*
      Mirrors your Python extract_amount():
      - removes commas
      - removes dollar signs
      - handles blank/null/nan/none
      - handles accounting negatives like (2.50)
    */

    IF p_text IS NULL THEN
        RETURN NULL;
    END IF;

    v_text := trim(p_text);

    IF v_text = ''
       OR lower(v_text) IN ('nan', 'none', 'null') THEN
        RETURN NULL;
    END IF;

    v_text := replace(v_text, ',', '');
    v_text := replace(v_text, '$', '');
    v_text := trim(v_text);

    IF v_text LIKE '(%' AND v_text LIKE '%)' THEN
        v_text := '-' || substring(v_text FROM 2 FOR length(v_text) - 2);
    END IF;

    v_text := trim(v_text);

    IF v_text ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
        RETURN v_text::numeric;
    END IF;

    RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION reporting._to_numeric_plain(p_text text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_text text;
BEGIN
    /*
      Mirrors:
      pd.to_numeric(value.astype(str).str.replace(',', ''), errors='coerce')
    */

    IF p_text IS NULL THEN
        RETURN NULL;
    END IF;

    v_text := replace(trim(p_text), ',', '');

    IF v_text = ''
       OR lower(v_text) IN ('nan', 'none', 'null') THEN
        RETURN NULL;
    END IF;

    IF v_text ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
        RETURN v_text::numeric;
    END IF;

    RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION reporting._parse_billing_date(p_text text)
RETURNS date
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_text text;
BEGIN
    /*
      Converts BILLINGDATE to date.

      Handles common formats:
      - 2025-07-01
      - 2025/07/01
      - 20250701
      - 202507
      - 07/01/2025
      - 07-01-2025

      If your BILLINGDATE is already date/timestamp in the table,
      to_jsonb still passes it as text and this function converts it.
    */

    IF p_text IS NULL THEN
        RETURN NULL;
    END IF;

    v_text := trim(p_text);

    IF v_text = ''
       OR lower(v_text) IN ('nan', 'none', 'null') THEN
        RETURN NULL;
    END IF;

    v_text := replace(v_text, '/', '-');

    BEGIN
        IF v_text ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN
            RETURN v_text::date;
        END IF;

        IF v_text ~ '^[0-9]{8}$' THEN
            RETURN to_date(v_text, 'YYYYMMDD');
        END IF;

        IF v_text ~ '^[0-9]{6}$' THEN
            RETURN to_date(v_text || '01', 'YYYYMMDD');
        END IF;

        IF v_text ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}$' THEN
            RETURN to_date(v_text, 'MM-DD-YYYY');
        END IF;

        RETURN v_text::date;

    EXCEPTION
        WHEN others THEN
            RETURN NULL;
    END;
END;
$$;


CREATE OR REPLACE FUNCTION reporting.validate_rogers_wireline_prices(
    p_billing_date date DEFAULT NULL
)
RETURNS TABLE
(
    "Billing Date" date,
    "Price Book Service ID" text,
    "Monthly Report Service ID" text,
    "Product Line" text,
    "Match Status (Service ID)" text,
    "Monthly Fixed Fee (from the Price Book)" numeric,
    "Report Rate" numeric,
    "Quantity" text,
    "Billed Amount (Pre-Tax)" numeric,
    "Difference (Rate - Monthly Fixed Fee)" numeric
)
LANGUAGE sql
AS $$
WITH price_source AS
(
    SELECT to_jsonb(p) AS row_json
    FROM raw_data.raw_rogers_data_pricebook p

    UNION ALL

    SELECT to_jsonb(v) AS row_json
    FROM raw_data.raw_rogers_voice_pricebook v
),

price_clean AS
(
    SELECT
        reporting._get_col_text(
            row_json,
            ARRAY['Service ID']
        ) AS price_book_service_id,

        trim(
            reporting._get_col_text(
                row_json,
                ARRAY['Service ID']
            )
        ) AS normalized_service_id,

        reporting._parse_money(
            reporting._get_col_text(
                row_json,
                ARRAY['Monthly Fixed Fee']
            )
        ) AS monthly_fixed_fee_numeric
    FROM price_source
),

report_source AS
(
    SELECT
        row_number() OVER () AS report_row,
        to_jsonb(r) AS row_json
    FROM raw_data.raw_rogers_spend_data_voice r
),

report_prepared AS
(
    SELECT
        report_row,

        reporting._parse_billing_date(
            reporting._get_col_text(
                row_json,
                ARRAY['BILLINGDATE', 'Billing Date', 'BillingDate']
            )
        ) AS billing_date,

        reporting._get_col_text(
            row_json,
            ARRAY['SERVICE_ID', 'Service ID']
        ) AS monthly_report_service_id,

        trim(
            reporting._get_col_text(
                row_json,
                ARRAY['SERVICE_ID', 'Service ID']
            )
        ) AS normalized_service_id,

        reporting._get_col_text(
            row_json,
            ARRAY['PRODUCTLINE', 'Product Line']
        ) AS product_line,

        reporting._get_col_text(
            row_json,
            ARRAY['QUANTITY', 'Quantity']
        ) AS quantity,

        reporting._get_col_text(
            row_json,
            ARRAY['CHARGE_DESCRIPTION', 'Charge Description']
        ) AS charge_description,

        reporting._get_col_text(
            row_json,
            ARRAY['CHARGETYPE', 'Charge Type']
        ) AS charge_type,

        reporting._to_numeric_plain(
            reporting._get_col_text(
                row_json,
                ARRAY['RATE', 'Rate']
            )
        ) AS report_rate,

        reporting._extract_amount(
            reporting._get_col_text(
                row_json,
                ARRAY['BILLED_AMOUNT(PRE-TAX)', 'Billed Amount Pre-Tax', 'Billed Amount (Pre-Tax)']
            )
        ) AS billed_amount_numeric
    FROM report_source
),

report_non_zero AS
(
    SELECT *
    FROM report_prepared
    WHERE abs(coalesce(billed_amount_numeric, 0)) > 0.005
      AND (
            p_billing_date IS NULL
            OR billing_date = p_billing_date
          )
),

report_with_service_id AS
(
    SELECT *
    FROM report_non_zero
    WHERE coalesce(trim(monthly_report_service_id), '') <> ''
),

missing_service_id_from_report AS
(
    SELECT
        billing_date,
        NULL::text AS price_book_service_id,
        monthly_report_service_id,
        product_line,
        'Missing Service ID from Report'::text AS match_status_service_id,
        NULL::numeric AS monthly_fixed_fee_from_price_book,
        report_rate,
        quantity,
        billed_amount_numeric AS billed_amount_pre_tax,
        NULL::numeric AS difference_rate_minus_monthly_fixed_fee
    FROM report_non_zero
    WHERE coalesce(trim(monthly_report_service_id), '') = ''
),

comparison AS
(
    SELECT
        r.billing_date,
        pc.price_book_service_id,
        r.monthly_report_service_id,
        r.product_line,

        CASE
            WHEN pc.monthly_fixed_fee_numeric IS NULL
                THEN 'Missing from Price Book'

            WHEN r.report_rate IS NULL
                THEN 'Missing Report Rate'

            WHEN abs(r.report_rate - pc.monthly_fixed_fee_numeric) <= 0.005
                THEN 'Matched'

            ELSE 'Rate Mismatch'
        END AS match_status_service_id,

        pc.monthly_fixed_fee_numeric AS monthly_fixed_fee_from_price_book,
        r.report_rate,
        r.quantity,
        r.billed_amount_numeric AS billed_amount_pre_tax,

        CASE
            WHEN pc.monthly_fixed_fee_numeric IS NULL
              OR r.report_rate IS NULL
                THEN NULL

            ELSE r.report_rate - pc.monthly_fixed_fee_numeric
        END AS difference_rate_minus_monthly_fixed_fee

    FROM report_with_service_id r
    LEFT JOIN price_clean pc
        ON r.normalized_service_id = pc.normalized_service_id
),

complete_comparison AS
(
    SELECT *
    FROM comparison

    UNION ALL

    SELECT *
    FROM missing_service_id_from_report
)

SELECT
    billing_date AS "Billing Date",
    price_book_service_id AS "Price Book Service ID",
    monthly_report_service_id AS "Monthly Report Service ID",
    product_line AS "Product Line",
    match_status_service_id AS "Match Status (Service ID)",
    monthly_fixed_fee_from_price_book AS "Monthly Fixed Fee (from the Price Book)",
    report_rate AS "Report Rate",
    quantity AS "Quantity",
    billed_amount_pre_tax AS "Billed Amount (Pre-Tax)",
    difference_rate_minus_monthly_fixed_fee AS "Difference (Rate - Monthly Fixed Fee)"
FROM complete_comparison;
$$;




