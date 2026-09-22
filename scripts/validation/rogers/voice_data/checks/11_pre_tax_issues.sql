-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 11) Total_Amount_Pre-Tax_Issues: TOTALAMOUNT minus taxes does not reconcile to PRE-TAX.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_pre_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE ABS((totalamount - gst_value - pst_value) - billed_amount_pre_tax) > 0.01
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;
