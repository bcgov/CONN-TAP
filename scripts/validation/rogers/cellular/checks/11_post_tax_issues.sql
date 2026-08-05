-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 11) Total_Amount_Post-Tax_Issues: PRE-TAX plus taxes does not reconcile to POST-TAX.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_post_tax_issues(p_month date DEFAULT NULL)
RETURNS SETOF raw_data.v_rogers_cellular_validated
LANGUAGE sql AS $$
    SELECT *
    FROM raw_data.v_rogers_cellular_validated
    WHERE ABS(
            (billed_amount_pre_tax + gst_value + pst_value + hst_value)
            - billed_amount_post_tax
          ) > 0.01
      AND (p_month IS NULL OR date_trunc('month', invoice_date::date) = date_trunc('month', p_month))
$$;
