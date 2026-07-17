WITH base AS (

    SELECT
        r.*,

----- normalize fields-----------------------------------
        NULLIF(TRIM(UPPER(bge)), '') AS bge_norm,
        NULLIF(TRIM(UPPER(sub_bge)), '') AS sub_bge_norm,
        NULLIF(TRIM(UPPER(productline)), '') AS productline_norm,

        COALESCE(gst, 0) AS gst_value,
        COALESCE(pst, 0) AS pst_value,

------ full row hash for exact duplicate detection ---------
        md5(row(r.*)::text) AS row_hash

    FROM raw_data.raw_rogers_spend_data_voice r

    
),

-- BGE MAP --------------------------------------------	
bge_map AS (

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

-- SUB_BGE MAP------------------------------------------
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

-- APPLY MAPPING --------------------------------------
mapped AS (

    SELECT
        b.*,

        COALESCE(bm.mapped_bge, b.bge_norm) AS bge_original,

        sm.expected_bge,

        COALESCE(
            sm.expected_bge,
            COALESCE(bm.mapped_bge, b.bge_norm)
        ) AS bge_actual

    FROM base b

    LEFT JOIN bge_map bm
        ON b.bge_norm = bm.raw_bge

    LEFT JOIN sub_bge_map sm
        ON b.sub_bge_norm = sm.sub_bge

),

-- DUPLICATE COUNTS --------------------------------------
duplicate_check AS (

    SELECT
        row_hash,
        COUNT(*) AS duplicate_count

    FROM mapped

    GROUP BY row_hash

),

-- FINAL VALIDATION ----------------------------------------
final AS (

    SELECT
        m.*,

        dc.duplicate_count,

---------- duplicate issue
        CASE
            WHEN dc.duplicate_count > 1
            THEN 'Duplicate Row'
        END AS duplicate_issue,

---------- missing sub_bge
        CASE
            WHEN sub_bge_norm IS NULL
             AND (
                    COALESCE(bge_norm, '') <> ''
                 
                 
                 OR COALESCE(totalamount, 0) <> 0
             )
            THEN 'Missing SUB-BGE'
        END AS missing_sub_bge_issue,

----------- missing bge
        CASE
            WHEN bge_actual IS NULL
            THEN 'Missing BGE'
        END AS missing_bge_issue,
---------- mapping issue
        CASE
            WHEN expected_bge IS NOT NULL
             AND bge_original <> expected_bge
            THEN 'Mapping Issue'
        END AS mapping_issue,


----------- productline validation
        CASE
            WHEN productline_norm NOT IN ('DATA', 'VOICE', 'N/A')
            THEN 'PRODUCTLINE Issue'
        END AS productline_issue,

        -- post-tax validation
        CASE
            WHEN ABS(
                (billed_amount_pre_tax + gst_value + pst_value)
                - totalamount
            ) > 0.01
            THEN 'Post-TAX Issue'
        END AS post_tax_issue,

--------- pre-tax validation
        CASE
            WHEN ABS(
                (totalamount - gst_value - pst_value)
                - billed_amount_pre_tax
            ) > 0.01
            THEN 'Pre-TAX Issue'
        END AS pre_tax_issue

    FROM mapped m

    LEFT JOIN duplicate_check dc
        ON m.row_hash = dc.row_hash
)

-- FINAL SUMMARY -------------------------------------------
SELECT
    billingdate,
    COALESCE(
        duplicate_issue,
        missing_sub_bge_issue,
        missing_bge_issue,
        mapping_issue,
        productline_issue,
        post_tax_issue,
        pre_tax_issue
    ) AS issue_type,

    sub_bge,
    bge_original,
    expected_bge,
    productline,

    COUNT(*) AS issue_count,

    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percent_of_total

FROM final

WHERE COALESCE(
        duplicate_issue,
        missing_sub_bge_issue,
        missing_bge_issue,
        mapping_issue,
        productline_issue,
        post_tax_issue,
        pre_tax_issue
    ) IS NOT NULL

GROUP BY
    billingdate,
    issue_type,
    sub_bge,
    bge_original,
    expected_bge,
    productline

ORDER BY
    issue_type,
    issue_count DESC;