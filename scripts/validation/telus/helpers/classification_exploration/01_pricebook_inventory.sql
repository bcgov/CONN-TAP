-- Telus pricebook table row counts and sample catalogue entries.

SELECT 'raw_telus_cellular_services_pricebook' AS tbl, COUNT(*) AS row_count
FROM raw_data.raw_telus_cellular_services_pricebook
UNION ALL
SELECT 'raw_telus_cellular_catalog_and_price_list_pricebook', COUNT(*)
FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook
UNION ALL
SELECT 'raw_telus_cellular_mms_pricebook', COUNT(*)
FROM raw_data.raw_telus_cellular_mms_pricebook
UNION ALL
SELECT 'raw_telus_control_center_services_pricebook', COUNT(*)
FROM raw_data.raw_telus_control_center_services_pricebook
UNION ALL
SELECT 'raw_telus_data_services_pricebook', COUNT(*)
FROM raw_data.raw_telus_data_services_pricebook
UNION ALL
SELECT 'raw_telus_voice_services_pricebook', COUNT(*)
FROM raw_data.raw_telus_voice_services_pricebook
ORDER BY 1;

-- All cellular pricebook service_ids
SELECT 'cellular_services' AS src, service_id, rate_plan, category
FROM raw_data.raw_telus_cellular_services_pricebook
UNION ALL
SELECT 'cellular_catalog', service_id, fee_based_optional_features, category
FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook
UNION ALL
SELECT 'cellular_mms', service_id, service, type_of_service
FROM raw_data.raw_telus_cellular_mms_pricebook
UNION ALL
SELECT 'control_center', service_id, rate_plan, category
FROM raw_data.raw_telus_control_center_services_pricebook
ORDER BY 1, 2;

-- Sample data pricebook
SELECT service_id, service_name, short_service_description, service_category
FROM raw_data.raw_telus_data_services_pricebook
ORDER BY service_id
LIMIT 15;

-- Sample voice pricebook
SELECT service_id, service_name, LEFT(short_service_description, 80) AS short_service_description, service_category
FROM raw_data.raw_telus_voice_services_pricebook
ORDER BY service_id
LIMIT 15;
