-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 8) Unknown_SUB-BGE: SUB-BGE values that resolve to neither a real SUB-BGE nor a real BGE.
-- A value matching a BGE alias (the org name repeated in the sub-BGE column, incl. seeded
-- school districts) is a known entity and excluded; anything else -- including unseeded
-- school districts -- surfaces here so it can be added to the seeds.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_unknown_sub_bge(p_month date DEFAULT NULL)
RETURNS TABLE (unknown_sub_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT v.sub_bge_norm::text
    FROM raw_data.v_rogers_cellular_validated v
    WHERE v.sub_bge_norm IS NOT NULL
      AND v.sub_bge_norm <> ''
      AND v.expected_bge IS NULL
      AND (p_month IS NULL OR date_trunc('month', v.invoice_date::date) = date_trunc('month', p_month))
      AND NOT EXISTS (
          SELECT 1
          FROM seeds.bge_alias_map bam
          WHERE raw_data.norm_key(bam.raw_name) = v.sub_bge_norm
      )
    ORDER BY 1
$$;
