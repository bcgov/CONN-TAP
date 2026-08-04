-- Rogers NGTA Data/Voice Validation -- the validated view that every check selects from.
--
-- Load this file before the numbered checks: they are declared RETURNS SETOF
-- raw_data.v_rogers_data_voice_validated or select from it, so it must exist first.
-- Mappings come from the DB seeds/reference data: seeds.bge_alias_map, seeds.sub_bge_alias_map,
-- reference_data.bge/sub_bge. Name matching uses raw_data.norm_key(text) from
-- helpers/_shared.sql (applied first by the runner).
--
-- Differs from the cellular validation: date is billingdate, taxes are GST+PST only (no HST),
-- the post-tax total is `totalamount`, duplicates use a full-row hash, and there is an extra
-- PRODUCTLINE check (DATA / VOICE / N/A).

CREATE OR REPLACE VIEW raw_data.v_rogers_data_voice_validated AS
WITH bge_map AS (

    SELECT raw_data.norm_key(bam.raw_name) AS raw_bge,
           bam.bge_alias             AS mapped_bge
    FROM seeds.bge_alias_map AS bam

),

sub_bge_map AS (

    SELECT raw_data.norm_key(sbam.raw_name) AS sub_bge,
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

        -- Full-row hash for exact duplicate detection.
        md5(ROW(r.*)::text)                AS row_hash

    FROM raw_data.raw_rogers_spend_data_voice r

),

bge_mapped AS (

    SELECT
        n.*,
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original
    FROM normalized n
    LEFT JOIN bge_map bm ON n.bge_norm = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,
        sm.expected_bge,
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual
    FROM bge_mapped b
    LEFT JOIN sub_bge_map sm ON b.sub_bge_norm = sm.sub_bge

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
