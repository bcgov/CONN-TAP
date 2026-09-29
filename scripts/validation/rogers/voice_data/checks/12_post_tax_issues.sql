-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 12) Total_Amount_Post-Tax_Issues: PRE-TAX plus taxes does not reconcile to TOTALAMOUNT.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_post_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_data_voice_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_data_voice_validated
    WHERE ABS((billed_amount_pre_tax + gst_value + pst_value) - totalamount) > 0.01
      AND (p_month IS NULL OR date_trunc('month', billingdate::date) = date_trunc('month', p_month))
$$;
