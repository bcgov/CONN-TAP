-- Rogers NGTA Cellular Validation -- one check per file, applied in filename order by
-- cellular/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_cellular_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 4) Missing_BGEs: real BGEs (from reference data) that no report row resolves to.
-- Presence is tested against the FINAL resolved BGE (bge_actual), which includes SUB-BGE
-- routing -- so made-up routing targets like 'School Districts' (reached only via a
-- school-district SUB-BGE, never named in the BGE column) are correctly counted present.
CREATE OR REPLACE FUNCTION raw_data.rogers_cellular_missing_bges(p_month date DEFAULT NULL)
RETURNS TABLE (missing_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text
    FROM reference_data.bge b
    WHERE NOT EXISTS (
        SELECT 1
        FROM raw_data.v_rogers_cellular_validated v
        WHERE v.bge_actual = b.code
          AND (p_month IS NULL OR date_trunc('month', v.invoice_date::date) = date_trunc('month', p_month))
    )
    ORDER BY 1
$$;
