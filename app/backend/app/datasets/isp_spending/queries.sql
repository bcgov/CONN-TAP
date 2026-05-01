-- Named query blocks. Header format: `-- name: <key>`
-- Bind parameters use SQLAlchemy's `:param` style.

-- name: by_region_year
SELECT
    region,
    year,
    SUM(amount)::numeric(18,2) AS total_spend,
    COUNT(*)                   AS line_items
FROM analytics.isp_spending
WHERE (:region IS NULL OR region = :region)
  AND (:year   IS NULL OR year   = :year)
GROUP BY region, year
ORDER BY year DESC, total_spend DESC
LIMIT :limit

-- name: totals_by_region
SELECT
    region,
    SUM(amount)::numeric(18,2) AS total_spend
FROM analytics.isp_spending
WHERE (:region IS NULL OR region = :region)
GROUP BY region
ORDER BY total_spend DESC
LIMIT :limit
