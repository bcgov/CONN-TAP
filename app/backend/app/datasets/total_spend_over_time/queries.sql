-- name: fiscal
SELECT
    fiscal_year                                      AS year,
    fiscal_quarter                                   AS quarter,
    SUM(spend_amount)::numeric(19, 4)               AS total_spend,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6)  AS total_spend_millions
FROM staging.service_category_vendor_spend
GROUP BY fiscal_year, fiscal_quarter
ORDER BY fiscal_year, fiscal_quarter

-- name: calendar
SELECT
    calendar_year                                    AS year,
    calendar_quarter                                 AS quarter,
    SUM(spend_amount)::numeric(19, 4)               AS total_spend,
    (SUM(spend_amount) / 1000000.0)::numeric(19, 6)  AS total_spend_millions
FROM staging.service_category_vendor_spend
GROUP BY calendar_year, calendar_quarter
ORDER BY calendar_year, calendar_quarter
