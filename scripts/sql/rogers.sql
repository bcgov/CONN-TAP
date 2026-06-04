WITH bge_map AS (
  SELECT *
  FROM (VALUES
    ('BC LOTTERY', 'BCLC'),
    ('BC LOTTERY CORPORATION', 'BCLC'),
    ('BRITISH COLUMBIA LOTTERY CORPORATION', 'BCLC'),
    ('BRITISH COLOMBIA LOTTERY CORPORATION', 'BCLC'),

    ('BC HYDRO', 'BC Hydro'),
    ('BRITISH COLUMBIA HYDRO', 'BC Hydro'),
    ('BRITISH COLUMBIA HYDRO & POWER AUTHORITY', 'BC Hydro'),

    ('EDUCATION AND CHILD CARE', 'ECC'),
    ('MINISTRY OF EDUCATION', 'ECC'),
    ('MINISTRY OF EDUCATION AND CHILD CARE', 'ECC'),
    ('BC MIN EDUCATION & CHILD CARE', 'ECC'),
    ('BC MIN EDUCATION AND CHILD CARE', 'ECC'),

    ('FRASER HEALTH AUTHORITY', 'FHA'),
    ('INTERIOR HEALTH AUTHORITY', 'IHA'),
    ('NORTHERN HEALTH AUTHORITY', 'NHA'),
    ('INSURANCE CORPORATION OF BRITISH COLUMB.', 'ICBC'),
    ('INSURANCE CORPORATION OF BRITISH COLUMBIA', 'ICBC'),
    ('PROVINCIAL HEALTH SERVICES AUTHORITY', 'PHSA'),
    ('VANCOUVER COASTAL HEALTH AUTHORITY', 'VCHA'),
    ('PROVIDENCE HEALTH CARE', 'VCHA'),
    ('VANCOUVER ISLAND HEALTH AUTHORITY', 'VIHA'),

    ('BC GOVERNMENT MINISTRIES', 'Gov BC'),
    ('BC MIN ATTORNEY GENERAL', 'Gov BC'),
    ('BC MIN CITIZENS'' SERVICES', 'Gov BC'),
    ('BC MIN HOUSING AND MUNICIPAL AFFAIRS', 'Gov BC'),
    ('BC MIN INDIGENOUS RELATIONS & RECONCIL.', 'Gov BC'),
    ('BC MIN JOBS AND ECONOMIC GROWTH', 'Gov BC'),
    ('BC MIN LABOUR', 'Gov BC'),
    ('BC MIN POST-SECONDARY ED & FUTURE SKILLS', 'Gov BC'),
    ('BC MIN SOCIAL DEV & POVERTY REDUCTION', 'Gov BC'),
    ('BC MIN TOURISM, ARTS, CULTURE, AND SPORT', 'Gov BC'),
    ('BC MIN TRANSPORTATION & TRANSIT', 'Gov BC'),
    ('INDIGENOUS RELATIONS AND RECONCILIATION', 'Gov BC'),
    ('JOB ECONOMIC DEVELOPMENT AND INNOVATION', 'Gov BC'),
    ('LAND AND WATER BC INC', 'Gov BC'),
    ('MIN OF FINANCE BC', 'Gov BC'),
    ('MIN OF JOBS TOURISM & INNOVATION', 'Gov BC'),
    ('MIN OF LABOUR', 'Gov BC'),
    ('MIN OF SOCIAL DEVELOPMENT', 'Gov BC'),
    ('MINISTRY OF CITIZENS SERVICES', 'Gov BC'),
    ('MINISTRY OF INFRASTRUCTURE', 'Gov BC'),
    ('OFFICE OF THE PREMIER', 'Gov BC'),
    ('TRANSPORTATION AND TRANSIT', 'Gov BC')
  ) AS m(alias, entity_key)
),
src AS (
  SELECT
    c.bge,
    c.sub_bge,
    date_trunc('month', COALESCE(c.invoice_date, r.source_period))::date AS month_start,
    COALESCE(c.hardware, 0)::numeric AS amount,
    'cellular_hardware'::text AS bucket
  FROM raw_data.raw_rogers_spend_cellular c
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = c.ingestion_run_id
  WHERE r.provider = 'rogers'

  UNION ALL

  SELECT
    c.bge,
    c.sub_bge,
    date_trunc('month', COALESCE(c.invoice_date, r.source_period))::date AS month_start,
    COALESCE(c.billed_amount_pre_tax, 0)::numeric
      - COALESCE(c.hardware, 0)::numeric AS amount,
    'cellular_plans'::text AS bucket
  FROM raw_data.raw_rogers_spend_cellular c
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = c.ingestion_run_id
  WHERE r.provider = 'rogers'

  UNION ALL

  SELECT
    v.bge,
    v.sub_bge,
    date_trunc('month', COALESCE(v.billingdate, r.source_period))::date AS month_start,
    COALESCE(v.billed_amount_pre_tax, 0)::numeric AS amount,
    CASE
      WHEN upper(trim(COALESCE(v.productline, ''))) = 'DATA' THEN 'data'
      WHEN upper(trim(COALESCE(v.productline, ''))) = 'VOICE' THEN 'voice'
      ELSE 'other'
    END AS bucket
  FROM raw_data.raw_rogers_spend_data_voice v
  JOIN raw_data.ingestion_run r ON r.ingestion_run_id = v.ingestion_run_id
  WHERE r.provider = 'rogers'
),
normalized AS (
  SELECT
    s.bge,
    s.sub_bge,
    s.month_start,
    s.amount,
    s.bucket,
    upper(trim(COALESCE(s.bge, ''))) AS bge_key,
    upper(trim(COALESCE(s.sub_bge, ''))) AS sub_bge_key
  FROM src s
),
bucketed AS (
  SELECT
    COALESCE(
      CASE
        WHEN sub_bge_key LIKE 'SCHOOL DISTRICT%'
          OR sub_bge_key LIKE 'DISTRICT%'
          OR bge_key LIKE 'SCHOOL DISTRICT%'
          OR bge_key LIKE 'DISTRICT%'
          THEN 'School Districts'
        WHEN sub_bge_key LIKE '%FAMILY MAINTENANCE AGENCY%'
          OR sub_bge_key LIKE '%PUBLIC SERVICE AGENCY%'
          THEN 'Gov BC'
        ELSE NULL
      END,
      sub_map.entity_key,
      bge_map.entity_key
    ) AS entity_key,
    month_start,
    amount,
    bucket
  FROM normalized n
  LEFT JOIN bge_map sub_map ON sub_map.alias = n.sub_bge_key
  LEFT JOIN bge_map bge_map ON bge_map.alias = n.bge_key
  WHERE month_start IS NOT NULL
)
SELECT
  'rogers'::text AS provider,
  entity_key,
  month_start,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_hardware'), 0) AS cellular_hardware,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'cellular_plans'), 0) AS cellular_plans,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'data'), 0) AS data_spend,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'voice'), 0) AS voice_spend,
  COALESCE(SUM(amount) FILTER (WHERE bucket = 'other'), 0) AS other_spend,
  COALESCE(SUM(amount), 0) AS total_reported
FROM bucketed
WHERE entity_key IS NOT NULL
GROUP BY entity_key, month_start
ORDER BY month_start, entity_key;
