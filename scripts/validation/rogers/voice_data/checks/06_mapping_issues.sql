-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

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
