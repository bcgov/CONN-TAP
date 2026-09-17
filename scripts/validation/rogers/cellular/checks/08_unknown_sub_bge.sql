-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 8) Unknown_SUB-BGE: any non-blank SUB-BGE value that does not resolve, via
-- seeds.sub_bge_alias_map, to an actual reference_data.sub_bge record for that BGE.
-- This includes a BGE's own name repeated in the SUB-BGE column (e.g. 'BC Hydro' or
-- 'BC Lottery') -- that is not technically wrong, but it is not a real SUB-BGE either
-- (whether or not the BGE has real SUB-BGEs elsewhere, e.g. BC Hydro's Powertech/Power Ex),
-- so it is flagged the same as any other unrecognized value.
DROP FUNCTION IF EXISTS raw_data.rogers_cellular_unknown_sub_bge(date);
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
