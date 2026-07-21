-- organization_name / sub_organization_name are retained as degenerate debug
-- attributes (the resolved alias code) for lineage/tracing only; reports use the
-- ids and resolve display names live.
select
    spend_line_item_id,
    period_key,
    provider_id,
    bge_id,
    sub_bge_id,
    service_category_id,
    organization_name,
    sub_organization_name,
    source_system,
    source_table,
    raw_id,
    spend_amount
from {{ ref('int_service_spend_line_items') }}
