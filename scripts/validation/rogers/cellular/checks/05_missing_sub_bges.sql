-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 5) Missing_SUB_BGEs: real SUB-BGEs (from reference data) that no report row resolves to.
-- Expected list is reference_data.sub_bge (one row per real sub-BGE, with its parent BGE);
-- the alias map only tests presence, so alternate raw spellings never fan out as "missing".
-- Individual school districts are excluded for now (b.code <> 'School Districts') -- same
-- noisy-rollup concern as the top-level Missing_BGEs check, just applied per-district here.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_missing_sub_bges(p_month date DEFAULT NULL)
RETURNS TABLE (related_bge text, missing_sub_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text, sb.code::text
    FROM reference_data.sub_bge sb
    JOIN reference_data.bge b ON b.id = sb.bge_id
    WHERE b.code <> 'School Districts'
      AND NOT EXISTS (
        SELECT 1
        FROM raw_data.raw_rogers_spend_cellular r
        JOIN seeds.sub_bge_alias_map sbam
          ON raw_data.norm_key(sbam.raw_name) = raw_data.norm_key(r.sub_bge)
        WHERE sbam.sub_bge_alias = sb.code
          AND (p_month IS NULL OR date_trunc('month', r.invoice_date::date) = date_trunc('month', p_month))
    )
    ORDER BY 1, 2
$$;
