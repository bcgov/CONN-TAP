-- Rogers NGTA Cellular Validation -- SQL view + per-check functions.
-- run_validations.py (re)creates these, then calls each function into its own worksheet tab
-- (matching the legacy Python/Excel report). Mappings come from the DB seeds/reference data:
-- seeds.bge_alias_map, seeds.sub_bge_alias_map, reference_data.bge/sub_bge.

-- Name matching uses raw_data.norm_key(text) from _shared.sql (applied first by the runner).

CREATE OR REPLACE VIEW raw_data.v_rogers_cellular_validated AS
WITH bge_map AS (

    SELECT raw_data.norm_key(bam.raw_name) AS raw_bge,
           bam.bge_alias             AS mapped_bge
    FROM seeds.bge_alias_map AS bam

),

sub_bge_map AS (

    SELECT raw_data.norm_key(sbam.raw_name) AS sub_bge,
           b.code                     AS expected_bge
    FROM seeds.sub_bge_alias_map AS sbam
    JOIN reference_data.sub_bge  AS sb ON sb.code  = sbam.sub_bge_alias
    JOIN reference_data.bge      AS b  ON b.id     = sb.bge_id

),

normalized AS (

    SELECT
        r.*,
        raw_data.norm_key(r.bge) AS bge_norm,
        raw_data.norm_key(r.sub_bge) AS sub_bge_norm

    FROM raw_data.raw_rogers_spend_cellular r

),

bge_mapped AS (

    SELECT
        n.*,

-- Original mapped BGE (before SUB-BGE override)
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original

    FROM normalized n

    LEFT JOIN bge_map bm
        ON n.bge_norm = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,

        sm.expected_bge,

 -- Final corrected BGE after SUB-BGE logic
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual

    FROM bge_mapped b

    LEFT JOIN sub_bge_map sm
        ON b.sub_bge_norm = sm.sub_bge

),

validated AS (

    SELECT
        f.*,

        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value,
        COALESCE(hst, 0) AS hst_value

    FROM final_mapping f

)

SELECT
    v.*,

    -- Business-key duplicate group size.
    COUNT(*) OVER (
        PARTITION BY
            invoice_date,
            company_code,
            subscriber_no,
            billed_amount_pre_tax,
            billed_amount_post_tax
    ) AS dup_count

FROM validated v;


-- 1) Duplicates: every row in a business-key duplicate group.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_duplicates(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE dup_count > 1
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
    ORDER BY invoice_date, company_code, subscriber_no
$$;

-- 2) Null_BGE: rows whose raw BGE is null/blank.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_null_bge(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE (bge_norm IS NULL OR bge_norm = '')
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
$$;

-- 3) Null_SUB-BGE: rows whose raw SUB-BGE is null/blank.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_null_sub_bge(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE (sub_bge_norm IS NULL OR sub_bge_norm = '')
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
$$;

-- 4) Missing_BGEs: real BGEs (from reference data) that no report row resolves to.
-- Presence is tested against the FINAL resolved BGE (bge_actual), which includes SUB-BGE
-- routing -- so made-up routing targets like 'School Districts' (reached only via a
-- school-district SUB-BGE, never named in the BGE column) are correctly counted present.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_missing_bges(p_month date DEFAULT NULL)
RETURNS TABLE (missing_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text
    FROM reference_data.bge b
    WHERE NOT EXISTS (
        SELECT 1
        FROM raw_data.v_rogers_cellular_validated v
        WHERE v.bge_actual = b.code
          AND (p_month IS NULL OR date_trunc('month', v.invoice_date::date) = date_trunc('month', p_month))
    )
    ORDER BY 1
$$;

-- 5) Missing_SUB_BGEs: real SUB-BGEs (from reference data) that no report row resolves to.
-- Expected list is reference_data.sub_bge (one row per real sub-BGE, with its parent BGE);
-- the alias map only tests presence, so alternate raw spellings never fan out as "missing".
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_missing_sub_bges(p_month date DEFAULT NULL)
RETURNS TABLE (related_bge text, missing_sub_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text, sb.code::text
    FROM reference_data.sub_bge sb
    JOIN reference_data.bge b ON b.id = sb.bge_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM raw_data.raw_rogers_spend_cellular r
        JOIN seeds.sub_bge_alias_map sbam
          ON raw_data.norm_key(sbam.raw_name) = raw_data.norm_key(r.sub_bge)
        WHERE sbam.sub_bge_alias = sb.code
          AND (p_month IS NULL OR date_trunc('month', r.invoice_date::date) = date_trunc('month', p_month))
    )
    ORDER BY 1, 2
$$;

-- 6) Mapping_Issues: rows where the report BGE differs from the BGE expected by the SUB-BGE.
-- Only flagged when the reported BGE is itself a real reference BGE -- so a genuine conflict
-- (report names real BGE X, but the SUB-BGE belongs to real BGE Y) is caught, while by-design
-- routing through the transitional 'ECC' label (not a reference BGE) to 'School Districts' or
-- 'Gov BC' is not.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_mapping_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE expected_bge IS NOT NULL
      AND bge_original <> expected_bge
      AND bge_original IN (SELECT code FROM reference_data.bge)
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
    ORDER BY sub_bge_norm
$$;

-- 7) Mapping_Summary: the mapping issues rolled up by SUB-BGE / reported BGE / expected BGE.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_mapping_summary(p_month date DEFAULT NULL)
RETURNS TABLE (sub_bge text, bge_report text, expected_bge text, cnt bigint)
LANGUAGE sql AS $$
    SELECT sub_bge_norm::text, bge_original::text, expected_bge::text, COUNT(*)
    FROM raw_data.v_rogers_cellular_validated
    WHERE expected_bge IS NOT NULL
      AND bge_original <> expected_bge
      AND bge_original IN (SELECT code FROM reference_data.bge)
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
    GROUP BY sub_bge_norm, bge_original, expected_bge
    ORDER BY COUNT(*) DESC
$$;

-- 8) Unknown_SUB-BGE: any non-blank SUB-BGE value that does not resolve, via
-- seeds.sub_bge_alias_map, to an actual reference_data.sub_bge record for that BGE.
-- This includes a BGE's own name repeated in the SUB-BGE column (e.g. 'BC Hydro' or
-- 'BC Lottery') -- that is not technically wrong, but it is not a real SUB-BGE either
-- (whether or not the BGE has real SUB-BGEs elsewhere, e.g. BC Hydro's Powertech/Power Ex),
-- so it is flagged the same as any other unrecognized value.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_unknown_sub_bge(p_month date DEFAULT NULL)
RETURNS TABLE (bge text, unknown_sub_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT v.bge_original::text, v.sub_bge_norm::text
    FROM raw_data.v_rogers_cellular_validated v
    WHERE v.sub_bge_norm IS NOT NULL
      AND v.sub_bge_norm <> ''
      AND v.expected_bge IS NULL
      AND (p_month IS NULL OR date_trunc('month', v.invoice_date::date) = date_trunc('month', p_month))
    ORDER BY 1, 2
$$;

-- 9) New_BGEs: report BGE values with no alias mapping (unrecognized raw names).
-- A raw BGE is "recognized" when bge_alias_map has an alias for it -- regardless of whether
-- that alias also has a reference_data.bge row (e.g. ECC is aliased but not a reference code).
-- Only genuinely unmapped raw BGEs surface here.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_new_bges(p_month date DEFAULT NULL)
RETURNS TABLE (new_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT raw_data.norm_key(r.bge)::text
    FROM raw_data.raw_rogers_spend_cellular r
    WHERE r.bge IS NOT NULL
      AND raw_data.norm_key(r.bge) <> ''
      AND (p_month IS NULL OR date_trunc('month', r.invoice_date::date) = date_trunc('month', p_month))
      AND NOT EXISTS (
          SELECT 1 FROM seeds.bge_alias_map bam
          WHERE raw_data.norm_key(bam.raw_name) = raw_data.norm_key(r.bge)
      )
    ORDER BY 1
$$;

-- 10) Total_Amount_Pre-Tax_Issues: POST-TAX minus taxes does not reconcile to PRE-TAX.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_pre_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE ABS(
            (billed_amount_post_tax - gst_value - pst_value - hst_value)
            - billed_amount_pre_tax
          ) > 0.01
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
$$;

-- 11) Total_Amount_Post-Tax_Issues: PRE-TAX plus taxes does not reconcile to POST-TAX.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_post_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE ABS(
            (billed_amount_pre_tax + gst_value + pst_value + hst_value)
            - billed_amount_post_tax
          ) > 0.01
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
$$;

-- 12) New/Removed BGE and SUB-BGE detection (month-over-month).
-- Statuses: Newly Appeared, Unrecognized, New + Unrecognized, Removed, Still Removed.
DROP FUNCTION IF EXISTS raw_data.rogers_cellular_new_removed_detection(date);
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_new_removed_detection(p_month date DEFAULT NULL)
RETURNS TABLE (current_month date, entity_type text, raw_value text, status text)
LANGUAGE sql AS $$
    WITH bge_known AS (
        SELECT DISTINCT raw_data.norm_key(bam.raw_name) AS raw_name
        FROM seeds.bge_alias_map AS bam
    ),
    sub_bge_known AS (
        SELECT DISTINCT raw_data.norm_key(sbam.raw_name) AS raw_name
        FROM seeds.sub_bge_alias_map AS sbam
    ),
    -- Current month = the given p_month, or the newest invoice month when NULL.
    invoice_months AS (
        SELECT
            date_trunc('month', COALESCE(p_month, MAX(invoice_date::date)))                       AS current_month,
            date_trunc('month', COALESCE(p_month, MAX(invoice_date::date))) - interval '1 month'  AS prior_month,
            date_trunc('month', COALESCE(p_month, MAX(invoice_date::date))) - interval '2 months' AS two_months_ago
        FROM raw_data.raw_rogers_spend_cellular
        WHERE invoice_date IS NOT NULL
    ),
    current_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.current_month
    ),
    prior_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.prior_month
    ),
    current_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.current_month
    ),
    prior_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.prior_month
    ),
    two_months_ago_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.two_months_ago
    ),
    two_months_ago_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_cellular r
        CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.invoice_date::date) = m.two_months_ago
    )
    SELECT m.current_month::date, 'BGE'::text, cb.bge_norm::text,
        CASE
            WHEN NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
             AND NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)
                THEN 'New + Unrecognized'
            WHEN NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
                THEN 'Unrecognized'
            WHEN NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)
                THEN 'Newly Appeared'
        END::text
    FROM current_bges cb CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
       OR NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)

    UNION ALL

    SELECT m.current_month::date, 'Sub BGE'::text, csb.sub_bge_norm::text,
        CASE
            WHEN NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
             AND NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)
                THEN 'New + Unrecognized'
            WHEN NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
                THEN 'Unrecognized'
            WHEN NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)
                THEN 'Newly Appeared'
        END::text
    FROM current_sub_bges csb CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
       OR NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)

    UNION ALL

    SELECT m.current_month::date, 'BGE'::text, pb.bge_norm::text, 'Removed'::text
    FROM prior_bges pb CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM current_bges cb WHERE cb.bge_norm = pb.bge_norm)

    UNION ALL

    SELECT m.current_month::date, 'Sub BGE'::text, psb.sub_bge_norm::text, 'Removed'::text
    FROM prior_sub_bges psb CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM current_sub_bges csb WHERE csb.sub_bge_norm = psb.sub_bge_norm)

    UNION ALL

    SELECT m.current_month::date, 'BGE'::text, tma.bge_norm::text, 'Still Removed'::text
    FROM two_months_ago_bges tma CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM prior_bges   pb WHERE pb.bge_norm  = tma.bge_norm)
      AND NOT EXISTS (SELECT 1 FROM current_bges cb WHERE cb.bge_norm  = tma.bge_norm)

    UNION ALL

    SELECT m.current_month::date, 'Sub BGE'::text, tma.sub_bge_norm::text, 'Still Removed'::text
    FROM two_months_ago_sub_bges tma CROSS JOIN invoice_months m
    WHERE NOT EXISTS (SELECT 1 FROM prior_sub_bges   psb WHERE psb.sub_bge_norm = tma.sub_bge_norm)
      AND NOT EXISTS (SELECT 1 FROM current_sub_bges csb WHERE csb.sub_bge_norm = tma.sub_bge_norm)

    ORDER BY 2, 4, 3
$$;
