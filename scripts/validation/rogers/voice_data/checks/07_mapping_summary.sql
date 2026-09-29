-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

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
