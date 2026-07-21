WITH bge_map AS (

    SELECT UPPER(TRIM(bam.raw_name)) AS raw_bge,
           bam.bge_alias             AS mapped_bge
    FROM seeds.bge_alias_map AS bam

),

sub_bge_map AS (

    SELECT UPPER(TRIM(sbam.raw_name)) AS sub_bge,
           b.code                     AS expected_bge
    FROM seeds.sub_bge_alias_map AS sbam
    JOIN reference_data.sub_bge  AS sb ON sb.code  = sbam.sub_bge_alias
    JOIN reference_data.bge      AS b  ON b.id     = sb.bge_id

),

normalized AS (

    SELECT
        r.*,
        UPPER(TRIM(r.bge)) AS bge_norm,
        UPPER(TRIM(r.sub_bge)) AS sub_bge_norm

    FROM raw_data.raw_rogers_spend_cellular r

),

bge_mapped AS (

    SELECT
        n.*,

-- Original mapped BGE (before SUB-BGE override)
        COALESCE(bm.mapped_bge, n.bge_norm) AS bge_original

    FROM normalized n

    LEFT JOIN bge_map bm
        ON n.bge_norm = bm.raw_bge

),

final_mapping AS (

    SELECT
        b.*,

        sm.expected_bge,

 -- Final corrected BGE after SUB-BGE logic
        COALESCE(sm.expected_bge, b.bge_original) AS bge_actual

    FROM bge_mapped b

    LEFT JOIN sub_bge_map sm
        ON b.sub_bge_norm = sm.sub_bge

),

validated AS (

    SELECT
        f.*,

        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value,
        COALESCE(hst, 0) AS hst_value

    FROM final_mapping f

),

issues AS (

    SELECT
        *,

 -- Duplicate validation
        CASE
            WHEN COUNT(*) OVER (
                PARTITION BY
                    invoice_date,
                    company_code,
                    subscriber_no,
                    billed_amount_pre_tax,
                    billed_amount_post_tax
            ) > 1
            THEN 'Duplicate Row'
        END AS duplicate_issue,

 -- Missing BGE
        CASE
            WHEN bge_actual IS NULL
            THEN 'Missing BGE'
        END AS missing_bge_issue,

 -- Missing SUB-BGE
        CASE
            WHEN sub_bge_norm IS NULL
            THEN 'Missing SUB-BGE'
        END AS missing_sub_bge_issue,

  -- Correct mapping validation
        CASE
            WHEN expected_bge IS NOT NULL
             AND bge_original <> expected_bge
            THEN 'Mapping Issue'
        END AS mapping_issue,

  -- Unknown SUB-BGE
        CASE
            WHEN sub_bge_norm IS NOT NULL
             AND expected_bge IS NULL
            THEN 'Unknown SUB-BGE'
        END AS unknown_sub_bge_issue,


   -- Post-tax validation
        CASE
            WHEN ABS(
                (billed_amount_pre_tax + gst_value + pst_value + hst_value)
                - billed_amount_post_tax
            ) > 0.01
            THEN 'Post-TAX Issue'
        END AS post_tax_issue,

   -- Pre-tax validation
        CASE
            WHEN ABS(
                (billed_amount_post_tax - gst_value - pst_value - hst_value)
                - billed_amount_pre_tax
            ) > 0.01
            THEN 'Pre-TAX Issue'
        END AS pre_tax_issue

    FROM validated

),

final AS (

    SELECT
        *,

        CASE
            WHEN duplicate_issue IS NOT NULL THEN 'Duplicate Row'
            WHEN missing_bge_issue IS NOT NULL THEN 'Missing BGE'
            WHEN missing_sub_bge_issue IS NOT NULL THEN 'Missing SUB-BGE'
            WHEN mapping_issue IS NOT NULL THEN 'Mapping Issue'
            WHEN post_tax_issue IS NOT NULL THEN 'Post-TAX Issue'
            WHEN pre_tax_issue IS NOT NULL THEN 'Pre-TAX Issue'
        END AS issue_type

    FROM issues

)


-- SUMMARY RESULTS----------------------------------------


SELECT
    invoice_date,
    issue_type,

    sub_bge,

    bge_original,

    expected_bge,

    COUNT(*) AS issue_count,

    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percent_of_total

FROM final

WHERE issue_type IS NOT NULL

GROUP BY
    invoice_date,
    issue_type,
    sub_bge,
    bge_original,
    expected_bge

ORDER BY
    issue_type,
    issue_count DESC;


-- =============================================
-- NEW BGE / SUB-BGE DETECTION
-- Flags BGEs and Sub BGEs that are new, unrecognized, removed, or still absent.
-- Statuses:
--   Newly Appeared    - in current month, not in prior month, recognized in seeds
--   Unrecognized      - in current month, not in seeds (regardless of prior month)
--   New + Unrecognized- in current month, not in prior month, not in seeds
--   Removed           - in prior month, not in current month
--   Still Removed     - absent in both prior and current month (was removed last month)
-- =============================================

WITH bge_known AS (

    SELECT UPPER(TRIM(bam.raw_name)) AS raw_name
    FROM seeds.bge_alias_map    AS bam
    JOIN reference_data.bge     AS b ON b.code = bam.bge_alias

),

sub_bge_known AS (

    SELECT UPPER(TRIM(sbam.raw_name)) AS raw_name
    FROM seeds.sub_bge_alias_map AS sbam
    JOIN reference_data.sub_bge  AS sb ON sb.code = sbam.sub_bge_alias

),

invoice_months AS (
    SELECT
        MAX(date_trunc('month', invoice_date::date))                          AS current_month,
        MAX(date_trunc('month', invoice_date::date)) - interval '1 month'    AS prior_month,
        MAX(date_trunc('month', invoice_date::date)) - interval '2 months'   AS two_months_ago
    FROM raw_data.raw_rogers_spend_cellular
    WHERE invoice_date IS NOT NULL
),

current_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.bge)) AS bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.bge IS NOT NULL
      AND TRIM(r.bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.current_month
),

prior_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.bge)) AS bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.bge IS NOT NULL
      AND TRIM(r.bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.prior_month
),

current_sub_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.sub_bge)) AS sub_bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.sub_bge IS NOT NULL
      AND TRIM(r.sub_bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.current_month
),

prior_sub_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.sub_bge)) AS sub_bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.sub_bge IS NOT NULL
      AND TRIM(r.sub_bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.prior_month
),

two_months_ago_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.bge)) AS bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.bge IS NOT NULL
      AND TRIM(r.bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.two_months_ago
),

two_months_ago_sub_bges AS (
    SELECT DISTINCT UPPER(TRIM(r.sub_bge)) AS sub_bge_norm
    FROM raw_data.raw_rogers_spend_cellular r
    CROSS JOIN invoice_months m
    WHERE r.sub_bge IS NOT NULL
      AND TRIM(r.sub_bge) <> ''
      AND date_trunc('month', r.invoice_date::date) = m.two_months_ago
)

SELECT
    m.current_month::date AS current_month,
    'BGE'                 AS entity_type,
    cb.bge_norm           AS raw_value,
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
         AND NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)
            THEN 'New + Unrecognized'
        WHEN NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
            THEN 'Unrecognized'
        WHEN NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)
            THEN 'Newly Appeared'
    END AS status
FROM current_bges cb
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM bge_known  k  WHERE k.raw_name  = cb.bge_norm)
   OR NOT EXISTS (SELECT 1 FROM prior_bges pb WHERE pb.bge_norm = cb.bge_norm)

UNION ALL

SELECT
    m.current_month::date  AS current_month,
    'Sub BGE'              AS entity_type,
    csb.sub_bge_norm       AS raw_value,
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
         AND NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)
            THEN 'New + Unrecognized'
        WHEN NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
            THEN 'Unrecognized'
        WHEN NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)
            THEN 'Newly Appeared'
    END AS status
FROM current_sub_bges csb
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM sub_bge_known  k   WHERE k.raw_name       = csb.sub_bge_norm)
   OR NOT EXISTS (SELECT 1 FROM prior_sub_bges psb WHERE psb.sub_bge_norm = csb.sub_bge_norm)

UNION ALL

SELECT
    m.current_month::date AS current_month,
    'BGE'                 AS entity_type,
    pb.bge_norm           AS raw_value,
    'Removed'             AS status
FROM prior_bges pb
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM current_bges cb WHERE cb.bge_norm = pb.bge_norm)

UNION ALL

SELECT
    m.current_month::date AS current_month,
    'Sub BGE'             AS entity_type,
    psb.sub_bge_norm      AS raw_value,
    'Removed'             AS status
FROM prior_sub_bges psb
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM current_sub_bges csb WHERE csb.sub_bge_norm = psb.sub_bge_norm)

UNION ALL

-- Still Removed: absent in prior month AND still absent in current month
SELECT
    m.current_month::date AS current_month,
    'BGE'                 AS entity_type,
    tma.bge_norm          AS raw_value,
    'Still Removed'       AS status
FROM two_months_ago_bges tma
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM prior_bges   pb WHERE pb.bge_norm  = tma.bge_norm)
  AND NOT EXISTS (SELECT 1 FROM current_bges cb WHERE cb.bge_norm  = tma.bge_norm)

UNION ALL

SELECT
    m.current_month::date  AS current_month,
    'Sub BGE'              AS entity_type,
    tma.sub_bge_norm       AS raw_value,
    'Still Removed'        AS status
FROM two_months_ago_sub_bges tma
CROSS JOIN invoice_months m
WHERE NOT EXISTS (SELECT 1 FROM prior_sub_bges   psb WHERE psb.sub_bge_norm = tma.sub_bge_norm)
  AND NOT EXISTS (SELECT 1 FROM current_sub_bges csb WHERE csb.sub_bge_norm = tma.sub_bge_norm)

ORDER BY entity_type, status, raw_value;
