-- Rogers NGTA Data/Voice Validation -- one check per file, applied in filename order by
-- voice_data/run_validations.py, each into its own worksheet tab.
--
-- Reads raw_data.v_rogers_data_voice_validated (00_view_validated.sql, created first); name
-- matching uses raw_data.norm_key(text) from helpers/_shared.sql. p_month := NULL scans
-- every month; pass any date within a month to restrict to that month.

-- 9) New_BGEs: report BGE values with no alias mapping (unrecognized raw names).
CREATE OR REPLACE FUNCTION raw_data.rogers_data_voice_new_bges(p_month date DEFAULT NULL)
RETURNS TABLE (new_bge text)
LANGUAGE sql AS $$
    SELECT DISTINCT raw_data.norm_key(r.bge)::text
    FROM raw_data.raw_rogers_spend_data_voice r
    WHERE r.bge IS NOT NULL
      AND raw_data.norm_key(r.bge) <> ''
      AND (p_month IS NULL OR date_trunc('month', r.billingdate::date) = date_trunc('month', p_month))
      AND NOT EXISTS (
          SELECT 1 FROM seeds.bge_alias_map bam
          WHERE raw_data.norm_key(bam.raw_name) = raw_data.norm_key(r.bge)
      )
    ORDER BY 1
$$;
