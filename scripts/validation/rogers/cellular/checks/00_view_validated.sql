-- Rogers NGTA Cellular Validation -- the validated view that every check selects from.
--
-- Load this file before the numbered checks: they are declared RETURNS SETOF
-- raw_data.v_rogers_cellular_validated or select from it, so it must exist first.
-- Mappings come from the DB seeds/reference data: seeds.bge_alias_map, seeds.sub_bge_alias_map,
-- reference_data.bge/sub_bge. Name matching uses reference_data.match_key(text), as in dbt.
-- reference_data.norm_key(text) is only used to keep report labels readable.

-- Drop first: CREATE OR REPLACE VIEW can't insert a column (qst_value) mid-list on an
-- existing view. CASCADE drops the dependent check functions, which the later
-- checks/*.sql files recreate.
DROP VIEW IF EXISTS raw_data.v_rogers_cellular_validated CASCADE;

CREATE VIEW raw_data.v_rogers_cellular_validated AS
-- Collapse equivalent aliases to the same target before joining, so each spend row
-- appears once even when filler words or school-district spellings differ.
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
        reference_data.norm_key(r.bge) AS bge_norm,
        reference_data.norm_key(r.sub_bge) AS sub_bge_norm

    FROM raw_data.raw_rogers_spend_cellular r

),

bge_mapped AS (

    SELECT
        n.*,

-- Original mapped BGE (before SUB-BGE override)
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original

    FROM normalized n

    LEFT JOIN bge_map bm
        ON reference_data.match_key(n.bge) = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,

        sm.expected_bge,

 -- Final corrected BGE after SUB-BGE logic
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual

    FROM bge_mapped b

    LEFT JOIN sub_bge_map sm
        ON reference_data.match_key(b.sub_bge) = sm.sub_bge

),

validated AS (

    SELECT
        f.*,

        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value,
        COALESCE(hst, 0) AS hst_value,
        COALESCE(qst, 0) AS qst_value

    FROM final_mapping f

)

SELECT
    v.*,

    -- Business-key duplicate group size.
    COUNT(*) OVER (
        PARTITION BY
            invoice_date,
            company_code,
            subscriber_no,
            billed_amount_pre_tax,
            billed_amount_post_tax
    ) AS dup_count

FROM validated v;
