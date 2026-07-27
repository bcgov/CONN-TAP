-- Finest-grain rows for the summary table: one row per
-- (bge, sub_bge, service_category). The service layer rolls the sub_bge tree
-- (sub_org / service_designee) and pivots service categories into columns.
-- sub_bge columns are NULL for spend booked directly at the BGE.

-- The `scaffold` query enumerates the full predefined reference_data hierarchy
-- (every BGE + sub_bge, regardless of spend). The service layer seeds the table
-- from it and overlays the spend rows below, so entities with no data still show
-- up as zero rows instead of vanishing.

-- name: scaffold
SELECT
    bg.id               AS bge_id,
    bg.code             AS bge_code,
    bg.name             AS bge_name,
    sb.id               AS sub_bge_id,
    sb.name             AS sub_bge_name,
    sb.entity_type      AS entity_type,
    sb.parent_sub_bge_id AS parent_sub_bge_id
FROM reference_data.bge bg
LEFT JOIN reference_data.sub_bge sb ON sb.bge_id = bg.id

-- name: fiscal
SELECT
    bg.id                                               AS bge_id,
    bg.code                                             AS bge_code,
    bg.name                                             AS bge_name,
    sb.id                                               AS sub_bge_id,
    sb.name                                             AS sub_bge_name,
    sb.entity_type                                      AS entity_type,
    sb.parent_sub_bge_id                                AS parent_sub_bge_id,
    sc.code                                             AS service_category_code,
    sc.name                                             AS service_category_name,
    v.source_group                                      AS source_group,
    SUM(v.spend_amount)::numeric(19, 4)                 AS spend_amount,
    (SUM(v.spend_amount) / 1000000.0)::numeric(19, 6)   AS spend_millions
FROM analytics.bge_service_category_spend v
JOIN reference_data.bge bg ON bg.id = v.bge_id
JOIN reference_data.service_category sc ON sc.id = v.service_category_id
LEFT JOIN reference_data.sub_bge sb ON sb.id = v.sub_bge_id
WHERE (
        CAST(:period AS text) IS NULL
        OR (v.fiscal_year::text || '_' || v.fiscal_quarter::text) = ANY(CAST(:period AS text[]))
    )
GROUP BY
    bg.id, bg.code, bg.name,
    sb.id, sb.name, sb.entity_type, sb.parent_sub_bge_id,
    sc.code, sc.name,
    v.source_group

-- name: calendar
SELECT
    bg.id                                               AS bge_id,
    bg.code                                             AS bge_code,
    bg.name                                             AS bge_name,
    sb.id                                               AS sub_bge_id,
    sb.name                                             AS sub_bge_name,
    sb.entity_type                                      AS entity_type,
    sb.parent_sub_bge_id                                AS parent_sub_bge_id,
    sc.code                                             AS service_category_code,
    sc.name                                             AS service_category_name,
    v.source_group                                      AS source_group,
    SUM(v.spend_amount)::numeric(19, 4)                 AS spend_amount,
    (SUM(v.spend_amount) / 1000000.0)::numeric(19, 6)   AS spend_millions
FROM analytics.bge_service_category_spend v
JOIN reference_data.bge bg ON bg.id = v.bge_id
JOIN reference_data.service_category sc ON sc.id = v.service_category_id
LEFT JOIN reference_data.sub_bge sb ON sb.id = v.sub_bge_id
WHERE (
        CAST(:period AS text) IS NULL
        OR (v.calendar_year::text || '_' || v.calendar_quarter::text) = ANY(CAST(:period AS text[]))
    )
GROUP BY
    bg.id, bg.code, bg.name,
    sb.id, sb.name, sb.entity_type, sb.parent_sub_bge_id,
    sc.code, sc.name,
    v.source_group
