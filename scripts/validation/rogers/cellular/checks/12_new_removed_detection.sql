-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.raw_rogers_spend_cellular directly; name matching uses raw_data.norm_key(text)
-- from helpers/_shared.sql. p_month := NULL scans every month; pass any date within a month
-- to restrict to that month.

-- 12) New/Removed BGE and SUB-BGE detection (month-over-month).
--
-- Two independent questions, deliberately answered on two different bases:
--
--   RECOGNITION is about a raw SPELLING, so it compares raw text. The whole point is to catch
--   spellings the seeds do not have yet, and resolving first would silently discard exactly
--   those. A spelling is "recognized" when seeds.bge_alias_map / seeds.sub_bge_alias_map has a
--   row for it -- alias MEMBERSHIP only, not whether that alias resolves to reference_data,
--   because the maps intentionally carry aliases for retired / not-yet-loaded entities and
--   those are still known. Same rule as telus_raw_validate_new_sub_bges_in_accounts.
--
--   APPEARANCE / DISAPPEARANCE is about an ENTITY, so it compares the resolved canonical code
--   (bge_alias_map.bge_alias / sub_bge_alias_map.sub_bge_alias). Providers re-spell the same
--   organization constantly; comparing raw text made every rename read as one organization
--   leaving and another arriving. BGE resolves to the ALIAS TARGET, not the post-SUB-BGE
--   override BGE, which keeps 'ECC' a distinct entity and keeps this check independent of the
--   SUB-BGE routing chain.
--
-- Statuses, aligned with the Telus validators (telus_raw_validate_new_bges_in_sheets /
-- telus_raw_validate_new_sub_bges_in_accounts, which share this vocabulary):
--   'Unmapped'            -- spelling in the current month, absent last month, no alias row
--   'Persisting Unmapped' -- spelling in both months, still no alias row
--   'New Match'           -- resolved entity in the current month, absent last month
--   'Disappeared'         -- resolved entity last month, absent this month
--   'Still Disappeared'   -- resolved entity two months ago, absent last month and this month.
--                            Telus has no one-month equivalent; the 'Still' prefix follows
--                            telus_raw_validate_still_missing_bges_in_sheets.
--
-- The `entity` column therefore carries a canonical code for the last three statuses and the
-- raw spelling for the first two -- an unrecognized spelling has no canonical code by
-- definition. It replaces the old `raw_value`, which is no longer accurate for every row.
--
-- A new unseeded spelling for an organization already in the report yields TWO rows:
-- 'Unmapped' for the spelling, and 'Disappeared' for the entity it used to resolve under.
-- That is intended -- the entity's spend genuinely stopped resolving.

DROP FUNCTION IF EXISTS raw_data.rogers_cellular_new_removed_detection(date);
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_new_removed_detection(p_month date DEFAULT NULL)
RETURNS TABLE (current_month date, entity_type text, entity text, status text)
LANGUAGE sql AS $$
    -- Raw spelling -> canonical entity code. Doubles as the recognition set: a spelling is
    -- recognized exactly when it has a row here.
    WITH bge_resolve AS (
        SELECT DISTINCT raw_data.norm_key(bam.raw_name) AS raw_name,
               bam.bge_alias                            AS code
        FROM seeds.bge_alias_map AS bam
    ),
    sub_bge_resolve AS (
        SELECT DISTINCT raw_data.norm_key(sbam.raw_name) AS raw_name,
               sbam.sub_bge_alias                        AS code
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

    -- Raw spellings per month (recognition side).
    bge_raw_by_month AS (
        SELECT DISTINCT date_trunc('month', r.invoice_date::date) AS month,
               raw_data.norm_key(r.bge)                        AS value
        FROM raw_data.raw_rogers_spend_cellular r
        WHERE r.invoice_date IS NOT NULL AND r.bge IS NOT NULL AND TRIM(r.bge) <> ''
    ),
    sub_bge_raw_by_month AS (
        SELECT DISTINCT date_trunc('month', r.invoice_date::date) AS month,
               raw_data.norm_key(r.sub_bge)                    AS value
        FROM raw_data.raw_rogers_spend_cellular r
        WHERE r.invoice_date IS NOT NULL AND r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
    ),

    -- Resolved entities per month (appearance / disappearance side). Rows whose spelling has
    -- no alias contribute nothing here -- they are reported as 'Unmapped' instead.
    bge_by_month AS (
        SELECT DISTINCT date_trunc('month', r.invoice_date::date) AS month,
               br.code                                         AS value
        FROM raw_data.raw_rogers_spend_cellular r
        JOIN bge_resolve br ON br.raw_name = raw_data.norm_key(r.bge)
        WHERE r.invoice_date IS NOT NULL AND r.bge IS NOT NULL AND TRIM(r.bge) <> ''
    ),
    sub_bge_by_month AS (
        SELECT DISTINCT date_trunc('month', r.invoice_date::date) AS month,
               sbr.code                                        AS value
        FROM raw_data.raw_rogers_spend_cellular r
        JOIN sub_bge_resolve sbr ON sbr.raw_name = raw_data.norm_key(r.sub_bge)
        WHERE r.invoice_date IS NOT NULL AND r.sub_bge IS NOT NULL AND TRIM(r.sub_bge) <> ''
    )

    -- BGE: unrecognized spellings in the current month.
    SELECT m.current_month::date, 'BGE'::text, cur.value::text,
        CASE WHEN EXISTS (SELECT 1 FROM bge_raw_by_month p
                          WHERE p.month = m.prior_month AND p.value = cur.value)
             THEN 'Persisting Unmapped' ELSE 'Unmapped' END::text
    FROM invoice_months m
    JOIN bge_raw_by_month cur ON cur.month = m.current_month
    WHERE NOT EXISTS (SELECT 1 FROM bge_resolve br WHERE br.raw_name = cur.value)

    UNION ALL

    -- SUB-BGE: unrecognized spellings in the current month.
    SELECT m.current_month::date, 'Sub BGE'::text, cur.value::text,
        CASE WHEN EXISTS (SELECT 1 FROM sub_bge_raw_by_month p
                          WHERE p.month = m.prior_month AND p.value = cur.value)
             THEN 'Persisting Unmapped' ELSE 'Unmapped' END::text
    FROM invoice_months m
    JOIN sub_bge_raw_by_month cur ON cur.month = m.current_month
    WHERE NOT EXISTS (SELECT 1 FROM sub_bge_resolve sbr WHERE sbr.raw_name = cur.value)

    UNION ALL

    -- BGE: entity in the current month but not the prior month.
    SELECT m.current_month::date, 'BGE'::text, cur.value::text, 'New Match'::text
    FROM invoice_months m
    JOIN bge_by_month cur ON cur.month = m.current_month
    WHERE NOT EXISTS (SELECT 1 FROM bge_by_month p
                      WHERE p.month = m.prior_month AND p.value = cur.value)

    UNION ALL

    -- SUB-BGE: entity in the current month but not the prior month.
    SELECT m.current_month::date, 'Sub BGE'::text, cur.value::text, 'New Match'::text
    FROM invoice_months m
    JOIN sub_bge_by_month cur ON cur.month = m.current_month
    WHERE NOT EXISTS (SELECT 1 FROM sub_bge_by_month p
                      WHERE p.month = m.prior_month AND p.value = cur.value)

    UNION ALL

    -- BGE: entity in the prior month but not the current month.
    SELECT m.current_month::date, 'BGE'::text, pri.value::text, 'Disappeared'::text
    FROM invoice_months m
    JOIN bge_by_month pri ON pri.month = m.prior_month
    WHERE NOT EXISTS (SELECT 1 FROM bge_by_month c
                      WHERE c.month = m.current_month AND c.value = pri.value)

    UNION ALL

    -- SUB-BGE: entity in the prior month but not the current month.
    SELECT m.current_month::date, 'Sub BGE'::text, pri.value::text, 'Disappeared'::text
    FROM invoice_months m
    JOIN sub_bge_by_month pri ON pri.month = m.prior_month
    WHERE NOT EXISTS (SELECT 1 FROM sub_bge_by_month c
                      WHERE c.month = m.current_month AND c.value = pri.value)

    UNION ALL

    -- BGE: entity two months ago, absent in both months since.
    SELECT m.current_month::date, 'BGE'::text, tma.value::text, 'Still Disappeared'::text
    FROM invoice_months m
    JOIN bge_by_month tma ON tma.month = m.two_months_ago
    WHERE NOT EXISTS (SELECT 1 FROM bge_by_month p
                      WHERE p.month = m.prior_month   AND p.value = tma.value)
      AND NOT EXISTS (SELECT 1 FROM bge_by_month c
                      WHERE c.month = m.current_month AND c.value = tma.value)

    UNION ALL

    -- SUB-BGE: entity two months ago, absent in both months since.
    SELECT m.current_month::date, 'Sub BGE'::text, tma.value::text, 'Still Disappeared'::text
    FROM invoice_months m
    JOIN sub_bge_by_month tma ON tma.month = m.two_months_ago
    WHERE NOT EXISTS (SELECT 1 FROM sub_bge_by_month p
                      WHERE p.month = m.prior_month   AND p.value = tma.value)
      AND NOT EXISTS (SELECT 1 FROM sub_bge_by_month c
                      WHERE c.month = m.current_month AND c.value = tma.value)

    ORDER BY 2, 4, 3
$$;
