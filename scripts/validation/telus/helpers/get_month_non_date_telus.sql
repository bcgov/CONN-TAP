SELECT DISTINCT
    month            AS raw_month_value,
    statement_date,
    sheet_name
FROM raw_telus_spend
WHERE month IS NULL
   OR NOT (
        month ~ '^\d{4}-\d{2}(-\d{2})?$'                                  -- YYYY-MM or YYYY-MM-DD
     OR month ~* '^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'     -- Month name (Jan, February, etc.)
     OR month ~ '^\d{1,2}[\/\-]\d{4}$'                                    -- MM/YYYY or MM-YYYY
     OR month ~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'                 -- YYYY-MM-DD HH:MM:SS
  )
ORDER BY sheet_name, statement_date;