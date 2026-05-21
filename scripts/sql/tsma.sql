===================tsma_cellular_spend=====================

SELECT
    lcd_category AS entity_key,
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(COALESCE(billed_amt, 0)) AS amount
FROM public.tsma_wireless
WHERE ccyymm BETWEEN '202401' AND '202612'
  AND NULLIF(TRIM(COALESCE(lcd_category, '')), '') IS NOT NULL
GROUP BY lcd_category, ccyymm
ORDER BY lcd_category, month_start;

===================tsma_data_spend=====================

SELECT
    entity AS entity_key,
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(COALESCE(billed_amt, 0)) AS amount
FROM public.tsma_wireline
WHERE ccyymm BETWEEN '202401' AND '202612'
  AND tsma_service_tower IN ('Business Internet', 'Data - WAN')
  AND NULLIF(TRIM(COALESCE(entity, '')), '') IS NOT NULL
GROUP BY entity, ccyymm
ORDER BY entity, month_start;


====================tsma_voice_spend======================


SELECT
    entity AS entity_key,
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(COALESCE(billed_amt, 0)) AS amount
FROM public.tsma_wireline
WHERE ccyymm BETWEEN '202401' AND '202612'
  AND tsma_service_tower IN ('Conferencing', 'Long Distance', 'Voice')
  AND NULLIF(TRIM(COALESCE(entity, '')), '') IS NOT NULL
GROUP BY entity, ccyymm
ORDER BY entity, month_start;


==============tsma_mms_spend=========================


SELECT
    entity_name AS entity_key,
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(COALESCE(total, 0)) AS amount
FROM public.tsma_mms
WHERE ccyymm BETWEEN '202401' AND '202612'
  AND NULLIF(TRIM(COALESCE(entity_name, '')), '') IS NOT NULL
GROUP BY entity_name, ccyymm
ORDER BY entity_name, month_start;


==================tsma_voice_ivr_spend=====================

SELECT
    'Gov BC' AS entity_key,
    to_date(ccyymm || '01', 'YYYYMMDD') AS month_start,
    SUM(COALESCE(billed_amt, 0)) AS amount
FROM public.tsma_ivr
WHERE ccyymm BETWEEN '202401' AND '202612'
GROUP BY ccyymm
ORDER BY month_start;

