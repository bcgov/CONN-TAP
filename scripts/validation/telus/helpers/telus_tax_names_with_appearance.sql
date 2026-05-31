SELECT
    TRIM(detail_description)                                                         AS detail_description,
    statement_category,
    array_agg(DISTINCT month ORDER BY month)                                         AS months,
    array_agg(DISTINCT month || ' [' || COALESCE(sheet_name, 'N/A') || ']')         AS month_sheet_names
FROM raw_telus_spend
WHERE (
        TRIM(detail_description) ILIKE '%GST%'
     OR TRIM(detail_description) ILIKE '%PST%'
    )
  AND TRIM(statement_category) NOT LIKE '%Taxes%'
GROUP BY TRIM(detail_description), statement_category
ORDER BY 1, 2;
