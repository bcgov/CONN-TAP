-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 2) Null_BGE: rows whose raw BGE is null/blank.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_null_bge(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE (bge_norm IS NULL OR bge_norm = '')
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;
