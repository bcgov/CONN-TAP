-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 12) New/Removed BGE and SUB-BGE detection (month-over-month).
-- Statuses: Newly Appeared, Unrecognized, New + Unrecognized, Removed, Still Removed.
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
