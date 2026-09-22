-- Reference: shared expressions for Telus classification exploration.
-- Not meant to be executed standalone; copy into other queries as needed.

-- Normalize detail_description for exact text fallback matching:
--   LOWER(TRIM(REGEXP_REPLACE(
--     REGEXP_REPLACE(detail_description, '\*', '', 'g'),
--     '[^a-z0-9 ]', '', 'g'
--   )))

-- NG code extraction:
--   Data (numeric):  UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[0-9]{5})'))
--   Voice + cross:   UPPER(SUBSTRING(TRIM(detail_description) FROM '^(NG[A-Z0-9]{2,6})'))

-- Current source_id bucket (matches scripts/sql/telus.sql):
--   CASE
--     WHEN is_hw OR TRIM(source_id) = '164' THEN 'cellular_hardware'
--     WHEN TRIM(source) = 'Wireless' OR TRIM(source_id) = '130' THEN 'cellular_plans'
--     WHEN TRIM(source_id) IN ('1001', '103') THEN 'data'
--     WHEN TRIM(source_id) IN ('104', '102', '106') THEN 'voice'
--     ELSE 'other'
--   END

-- Standard spend filter (excludes taxes, payments, balance forward, hardware detail lines):
--   COALESCE(LOWER(TRIM(statement_section)), '') <> 'balance forward'
--   AND NOT raw_data.fn_telus_is_hardware_detail(detail_description)
--     (defined in helpers/telus_hardware_detail.sql -- matches on the description's word
--      signature, so variable amounts / terms / expiry dates need no entry of their own)
--   AND COALESCE(LOWER(TRIM(statement_category)), '') NOT IN (
--     'taxes', 'payment', 'payments', 'amount due from last bill'
--   )
