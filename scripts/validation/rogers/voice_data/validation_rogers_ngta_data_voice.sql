-- Rogers NGTA Data/Voice Validation -- SQL view + per-check functions.
-- run_validations.py (re)creates these, then calls each function into its own worksheet tab
-- (matching the legacy Python/Excel report). Mappings come from the DB seeds/reference data:
-- seeds.bge_alias_map, seeds.sub_bge_alias_map, reference_data.bge/sub_bge.
--
-- Differs from the cellular validation: date is billingdate, taxes are GST+PST only (no HST),
-- the post-tax total is `totalamount`, duplicates use a full-row hash, and there is an extra
-- PRODUCTLINE check (DATA / VOICE / N/A).

-- Name matching uses raw_data.norm_key(text) from _shared.sql (applied first by the runner).

CREATE OR REPLACE VIEW raw_data.v_rogers_data_voice_validated AS
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
        raw_data.norm_key(r.bge)           AS bge_norm,
        raw_data.norm_key(r.sub_bge)       AS sub_bge_norm,
        NULLIF(UPPER(TRIM(r.productline)), '') AS productline_norm,

        -- Full-row hash for exact duplicate detection.
        md5(ROW(r.*)::text)                AS row_hash

    FROM raw_data.raw_rogers_spend_data_voice r

),

bge_mapped AS (

    SELECT
        n.*,
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original
    FROM normalized n
    LEFT JOIN bge_map bm ON n.bge_norm = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,
        sm.expected_bge,
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual
    FROM bge_mapped b
    LEFT JOIN sub_bge_map sm ON b.sub_bge_norm = sm.sub_bge

),

validated AS (

    SELECT
        f.*,
        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value
    FROM final_mapping f

)

SELECT
    v.*,

    -- Full-row duplicate group size.
    COUNT(*) OVER (PARTITION BY row_hash) AS dup_count

FROM validated v;


-- 1) Duplicates: every row in a full-row duplicate group.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_duplicates(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE dup_count > 1
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 2) Null_BGE: rows whose raw BGE is null/blank.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_null_bge(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE (bge_norm IS NULL OR bge_norm = '')
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 3) Null_SUB-BGE: rows whose raw SUB-BGE is null/blank.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_null_sub_bge(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE (sub_bge_norm IS NULL OR sub_bge_norm = '')
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 4) Missing_BGEs: real BGEs (from reference data) that no report row resolves to.
-- Presence is tested against the FINAL resolved BGE (bge_actual), which includes SUB-BGE
-- routing -- so made-up routing targets like 'School Districts' are correctly counted present.
-- 'School Districts' itself is excluded outright: it's not a real billed org (see the
-- comment on that row in reference_data/bge.sql), just a rollup bucket for ~90 real
-- districts, so it going quiet for a month is far weaker signal than any other BGE
-- going quiet and shouldn't be reported as a validation gap.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_missing_bges(p_month date DEFAULT NULL)
RETURNS TABLE (missing_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text
    FROM reference_data.bge b
    WHERE b.code <> 'School Districts'
      AND NOT EXISTS (
        SELECT 1
        FROM raw_data.v_rogers_data_voice_validated v
        WHERE v.bge_actual = b.code
          AND (p_month IS NULL OR date_trunc('month', v.billingdate::date) = date_trunc('month', p_month))
    )
    ORDER BY 1
$$;

-- 5) Missing_SUB_BGEs: real SUB-BGEs (from reference data) that no report row resolves to.
-- Individual school districts are excluded for now (b.code <> 'School Districts') -- same
-- noisy-rollup concern as the top-level Missing_BGEs check, just applied per-district here.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_missing_sub_bges(p_month date DEFAULT NULL)
RETURNS TABLE (related_bge text, missing_sub_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text, sb.code::text
    FROM reference_data.sub_bge sb
    JOIN reference_data.bge b ON b.id = sb.bge_id
    WHERE b.code <> 'School Districts'
      AND NOT EXISTS (
        SELECT 1
        FROM raw_data.raw_rogers_spend_data_voice r
        JOIN seeds.sub_bge_alias_map sbam
          ON raw_data.norm_key(sbam.raw_name) = raw_data.norm_key(r.sub_bge)
        WHERE sbam.sub_bge_alias = sb.code
          AND (p_month IS NULL OR date_trunc('month', r.billingdate::date) = date_trunc('month', p_month))
    )
    ORDER BY 1, 2
$$;

-- 6) Mapping_Issues: rows where the report BGE differs from the BGE expected by the SUB-BGE.
-- Only flagged when the reported BGE is itself a real reference BGE, so by-design routing
-- through the transitional 'ECC' label (not a reference BGE) is not flagged.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_mapping_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE expected_bge IS NOT NULL
      AND bge_original <> expected_bge
      AND bge_original IN (SELECT code FROM reference_data.bge)
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
    ORDER BY sub_bge_norm
$$;

-- 7) Mapping_Summary: the mapping issues rolled up by SUB-BGE / reported BGE / expected BGE.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_mapping_summary(p_month date DEFAULT NULL)
RETURNS TABLE (sub_bge text, bge_report text, expected_bge text, cnt bigint)
LANGUAGE sql AS $$
    SELECT sub_bge_norm::text, bge_original::text, expected_bge::text, COUNT(*)
    FROM raw_data.v_rogers_data_voice_validated
    WHERE expected_bge IS NOT NULL
      AND bge_original <> expected_bge
      AND bge_original IN (SELECT code FROM reference_data.bge)
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
    GROUP BY sub_bge_norm, bge_original, expected_bge
    ORDER BY COUNT(*) DESC
$$;

-- 8) Unknown_SUB-BGE: SUB-BGE values that resolve to neither a real SUB-BGE nor a real BGE.
-- A value matching a BGE alias (org name repeated in the sub-BGE column, incl. seeded school
-- districts) is a known entity and excluded; anything else surfaces so it can be seeded.
DROP FUNCTION IF EXISTS raw_data.rogers_data_voice_unknown_sub_bge(date);
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_unknown_sub_bge(p_month date DEFAULT NULL)
RETURNS TABLE (unknown_sub_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT v.sub_bge_norm::text
    FROM raw_data.v_rogers_data_voice_validated v
    WHERE v.sub_bge_norm IS NOT NULL
      AND v.sub_bge_norm <> ''
      AND v.expected_bge IS NULL
      AND (p_month IS NULL OR date_trunc('month', v.billingdate::date) = date_trunc('month', p_month))
      AND NOT EXISTS (
          SELECT 1 FROM seeds.bge_alias_map bam
          WHERE raw_data.norm_key(bam.raw_name) = v.sub_bge_norm
      )
    ORDER BY 1
$$;

-- 9) New_BGEs: report BGE values with no alias mapping (unrecognized raw names).
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_new_bges(p_month date DEFAULT NULL)
RETURNS TABLE (new_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT raw_data.norm_key(r.bge)::text
    FROM raw_data.raw_rogers_spend_data_voice r
    WHERE r.bge IS NOT NULL
      AND raw_data.norm_key(r.bge) <> ''
      AND (p_month IS NULL OR date_trunc('month', r.billingdate::date) = date_trunc('month', p_month))
      AND NOT EXISTS (
          SELECT 1 FROM seeds.bge_alias_map bam
          WHERE raw_data.norm_key(bam.raw_name) = raw_data.norm_key(r.bge)
      )
    ORDER BY 1
$$;

-- 10) PRODUCTLINE_Issues: productline outside the allowed set (DATA / VOICE / N/A).
-- Null / blank / 'NULL' / 'NAN' are treated as N/A (valid), matching the Python validation.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_productline_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE COALESCE(NULLIF(NULLIF(productline_norm, 'NULL'), 'NAN'), 'N/A')
          NOT IN ('DATA', 'VOICE', 'N/A')
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 11) Total_Amount_Pre-Tax_Issues: TOTALAMOUNT minus taxes does not reconcile to PRE-TAX.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_pre_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE ABS((totalamount - gst_value - pst_value) - billed_amount_pre_tax) > 0.01
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 12) Total_Amount_Post-Tax_Issues: PRE-TAX plus taxes does not reconcile to TOTALAMOUNT.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_post_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE ABS((billed_amount_pre_tax + gst_value + pst_value) - totalamount) > 0.01
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;

-- 13) New/Removed BGE and SUB-BGE detection (month-over-month).
-- Statuses: Newly Appeared, Unrecognized, New + Unrecognized, Removed, Still Removed.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_new_removed_detection(p_month date DEFAULT NULL)
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
    -- Current month = the given p_month, or the newest billing month when NULL.
    invoice_months AS (
        SELECT
            date_trunc('month', COALESCE(p_month, MAX(billingdate::date)))                       AS current_month,
            date_trunc('month', COALESCE(p_month, MAX(billingdate::date))) - interval '1 month'  AS prior_month,
            date_trunc('month', COALESCE(p_month, MAX(billingdate::date))) - interval '2 months' AS two_months_ago
        FROM raw_data.raw_rogers_spend_data_voice
        WHERE billingdate IS NOT NULL
    ),
    current_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.current_month
    ),
    prior_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.prior_month
    ),
    current_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.current_month
    ),
    prior_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.prior_month
    ),
    two_months_ago_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.bge) AS bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.bge IS NOT NULL AND TRIM(r.bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.two_months_ago
    ),
    two_months_ago_sub_bges AS (
        SELECT DISTINCT raw_data.norm_key(r.sub_bge) AS sub_bge_norm
        FROM raw_data.raw_rogers_spend_data_voice r CROSS JOIN invoice_months m
        WHERE r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
          AND date_trunc('month', r.billingdate::date) = m.two_months_ago
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
