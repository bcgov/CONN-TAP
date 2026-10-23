-- Rogers NGTA Data/Voice Validation -- the validated view that every check selects from.
--
-- Load this file before the numbered checks: they are declared RETURNS SETOF
-- raw_data.v_rogers_data_voice_validated or select from it, so it must exist first.
-- Mappings come from the DB seeds/reference data: seeds.bge_alias_map, seeds.sub_bge_alias_map,
-- reference_data.bge/sub_bge. Name matching uses reference_data.match_key(text), as in dbt.
-- raw_data.norm_key(text) is only used to keep report labels readable.
--
-- Differs from the cellular validation: date is billingdate, taxes are GST+PST only (no HST),
-- the post-tax total is `totalamount`, duplicates use a full-row hash, and there is an extra
-- PRODUCTLINE check (DATA / VOICE / N/A).

CREATE OR REPLACE VIEW raw_data.v_rogers_data_voice_validated AS
WITH bge_map AS (

    SELECT DISTINCT reference_data.match_key(bam.raw_name) AS raw_bge,
           bam.bge_alias             AS mapped_bge
    FROM seeds.bge_alias_map AS bam

),

sub_bge_map AS (

    SELECT DISTINCT reference_data.match_key(sbam.raw_name) AS sub_bge,
           b.code                     AS expected_bge
    FROM seeds.sub_bge_alias_map AS sbam
    JOIN reference_data.sub_bge  AS sb ON sb.code  = sbam.sub_bge_alias
    JOIN reference_data.bge      AS b  ON b.id     = sb.bge_id

),

normalized AS (

    SELECT
        r.*,
        raw_data.norm_key(r.bge)           AS bge_norm,
        raw_data.norm_key(r.sub_bge)       AS sub_bge_norm,
        NULLIF(UPPER(TRIM(r.productline)), '') AS productline_norm,

        -- Full-row hash for exact duplicate detection, following the original Python check:
        -- every file column compared as trimmed text. raw_id and ingestion_run_id are load
        -- metadata, not file columns, so they are excluded (raw_id is unique per row and made
        -- every hash distinct). Nulls stay distinct from blanks, as 'nan' did in pandas.
        (SELECT md5(string_agg(j.key || '=' || COALESCE(btrim(j.value), '<null>'), '|' ORDER BY j.key))
         FROM jsonb_each_text(to_jsonb(r) - 'raw_id' - 'ingestion_run_id') AS j
        )                                  AS row_hash

    FROM raw_data.raw_rogers_spend_data_voice r

),

bge_mapped AS (

    SELECT
        n.*,
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original
    FROM normalized n
    LEFT JOIN bge_map bm ON reference_data.match_key(n.bge) = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,
        sm.expected_bge,
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual
    FROM bge_mapped b
    LEFT JOIN sub_bge_map sm ON reference_data.match_key(b.sub_bge) = sm.sub_bge

),

validated AS (

    SELECT
        f.*,
        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value
    FROM final_mapping f

)

SELECT
    v.*,

    -- Full-row duplicate group size.
    COUNT(*) OVER (PARTITION BY row_hash) AS dup_count

FROM validated v;
