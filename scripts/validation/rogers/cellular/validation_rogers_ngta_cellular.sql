WITH bge_map AS (

    SELECT *
    FROM (VALUES
        ('BRITISH COLUMBIA LOTTERY CORPORATION', 'BCLC'),
        ('BRITISH COLOMBIA LOTTERY CORPORATION', 'BCLC'),
        ('BC LOTTERY CORPORATION', 'BCLC'),
        ('BC LOTTERY', 'BCLC'),
        ('BC HYDRO', 'BC HYDRO'),
        ('BRITISH COLUMBIA HYDRO', 'BC HYDRO'),
        ('EDUCATION AND CHILD CARE', 'ECC'),
        ('FRASER HEALTH AUTHORITY', 'FHA'),
        ('INTERIOR HEALTH AUTHORITY', 'IHA'),
        ('NORTHERN HEALTH AUTHORITY', 'NHA'),
        ('INSURANCE CORPORATION OF BRITISH COLUMB.', 'ICBC'),
        ('PROVINCIAL HEALTH SERVICES AUTHORITY', 'PHSA'),
        ('VANCOUVER COASTAL HEALTH AUTHORITY', 'VCHA'),
        ('PROVIDENCE HEALTH CARE', 'PHC'),
        ('VANCOUVER ISLAND HEALTH AUTHORITY', 'VIHA'),
        ('BC GOVERNMENT MINISTRIES', 'GOV BC')
    ) AS t(raw_bge, mapped_bge)

),

sub_bge_map AS (

    SELECT *
    FROM (VALUES
        ('BC MIN ATTORNEY GENERAL', 'GOV BC'),
        ('INDIGENOUS RELATIONS AND RECONCILIATION', 'GOV BC'),
        ('MINISTRY OF CITIZENS SERVICES', 'GOV BC'),
        ('MINISTRY OF INFRASTRUCTURE', 'GOV BC'),
        ('MIN OF SOCIAL DEVELOPMENT', 'GOV BC'),
        ('BC MIN AGRICULTURE & FOOD', 'GOV BC'),
        ('BC MIN CHILDREN & FAMILY DEVELOPMENT', 'GOV BC'),
        ('BC MIN EDUCATION & CHILDCARE', 'GOV BC'),
        ('BC MIN EMERG MGMT & CLIMATE READINESS', 'GOV BC'),
        ('BC MIN ENERGY & CLIMATE SOLUTIONS', 'GOV BC'),
        ('BC MIN ENVIRONMENT AND PARKS', 'GOV BC'),
        ('BC MIN FINANCE', 'GOV BC'),
        ('BC MIN FORESTS', 'GOV BC'),
        ('BC MIN HEALTH', 'GOV BC'),
        ('BC MIN HOUSING & MUNICIPAL AFFAIRS', 'GOV BC'),
        ('BC MIN JOBS & ECONOMIC GROWTH', 'GOV BC'),
        ('BC MIN LABOUR', 'GOV BC'),
        ('BC MIN MINING & CRITICAL MINERALS', 'GOV BC'),
        ('BC MIN POST-SECONDARY ED & FUTURE SKILLS', 'GOV BC'),
        ('BC MIN PUBLIC SAFETY & SOLICITOR GEN', 'GOV BC'),
        ('BC MIN SOCIAL DEV & POVERTY REDUCTION', 'GOV BC'),
        ('BC MIN TOURISM, ARTS, CULTURE, AND SPORT', 'GOV BC'),
        ('BC MIN TRANSPORTATION & TRANSIT', 'GOV BC'),
        ('BC MIN WATER LAND & RESOURCE STEWARD', 'GOV BC'),
        ('BC OFFICE OF THE PREMIER', 'GOV BC'),
        ('BC PUBLIC SERVICE AGENCY', 'GOV BC'),
        ('BC ASSESSMENT', 'GOV BC'),
        ('BC LDB', 'GOV BC'),
        ('BC FAMILY MAINTENANCE AGENCY LTD.', 'GOV BC'),
        ('BC FINANCIAL SERVICES AUTHORITY', 'GOV BC'),
        ('POWERTECH', 'BC HYDRO'),
        ('POWER EX', 'BC HYDRO')
    ) AS t(sub_bge, expected_bge)

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



=======
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