-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 4) Missing_BGEs: real BGEs (from reference data) that no report row resolves to.
-- Presence is tested against the FINAL resolved BGE (bge_actual), which includes SUB-BGE
-- routing -- so made-up routing targets like 'School Districts' are correctly counted present.
-- 'School Districts' itself is excluded outright: it's not a real billed org (see the
-- comment on that row in reference_data/bge.sql), just a rollup bucket for ~90 real
-- districts, so it going quiet for a month is far weaker signal than any other BGE
-- going quiet and shouldn't be reported as a validation gap.
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_missing_bges(p_month date DEFAULT NULL)
RETURNS TABLE (missing_bge text)
LANGUAGE sql AS $$
    SELECT b.code::text
    FROM reference_data.bge b
    WHERE b.code <> 'School Districts'
      AND NOT EXISTS (
        SELECT 1
        FROM raw_data.v_rogers_data_voice_validated v
        WHERE v.bge_actual = b.code
          AND (p_month IS NULL OR date_trunc('month', v.billingdate::date) = date_trunc('month', p_month))
    )
    ORDER BY 1
$$;
