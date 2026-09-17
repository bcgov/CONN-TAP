-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

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
