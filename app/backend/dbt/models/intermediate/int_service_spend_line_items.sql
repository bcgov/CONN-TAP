{{ config(materialized='view') }}

-- Rogers
with rogers as (
    select * from {{ ref('int_rogers_ngta_spend') }}
),

-- Telus
telus_ngta as (
    select * from {{ ref('int_telus_ngta_spend') }}
),

-- TSMA and TSMA Lite
tsma as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        organization_name,
        sub_organization_name,
        coalesce(tsma_service_tower, source_service_family) as lookup_code,
        spend_amount
    from {{ ref('stg_tsma_spend') }}
),

-- TSMA Other
tsma_other as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        organization_name,
        sub_organization_name,
        source_service_family as lookup_code,
        spend_amount
    from {{ ref('stg_tsma_other_spend') }}
),

unioned as (
    select * from rogers
    union all
    select * from telus_ngta
    union all
    select * from tsma
    union all
    select * from tsma_other
),

-- ECC is not a BGE in our system -- it's a ministry under Gov BC. Reports show it at
-- BGE level, so we rewrite those rows here (school districts under ECC are already
-- split to 'School Districts' upstream, so only ministry spend is left as 'ECC').
unioned_ecc_fixed as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        case when organization_name = 'ECC' then 'Gov BC' else organization_name end as organization_name,
        case when organization_name = 'ECC' then 'Education and Child Care' else sub_organization_name end as sub_organization_name,
        lookup_code,
        spend_amount
    from unioned
)

select
    md5(concat_ws('|', u.vendor, u.source_system, u.source_table, u.raw_id::text)) as spend_line_item_id,
    p.id        as provider_id,
    u.source_system,
    u.source_table,
    u.raw_id,
    u.month_start as period_key,
    u.organization_name,
    u.sub_organization_name,
    coalesce(sb.bge_id, b.id) as bge_id,
    sc.service_category_id,
    sb.id       as sub_bge_id,
    u.spend_amount
from unioned_ecc_fixed u
left join {{ source('reference_data', 'service_code') }} sc
    on sc.source_system = u.source_system
    and sc.code = u.lookup_code
left join {{ source('reference_data', 'provider') }} p on p.code = u.vendor
-- organization_name / sub_organization_name arrive already alias-resolved from the
-- staging models, so here we only resolve the canonical code to its reference id.
left join {{ source('reference_data', 'bge') }} b on reference_data.norm_key(b.code) = reference_data.norm_key(u.organization_name)
left join {{ source('reference_data', 'sub_bge') }} sb on reference_data.norm_key(sb.code) = reference_data.norm_key(u.sub_organization_name)
where u.month_start is not null
    and u.spend_amount <> 0
