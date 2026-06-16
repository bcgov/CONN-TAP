{{ config(materialized='view') }}

-- Rogers
with rogers as (
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
    from {{ ref('stg_rogers_spend') }}
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
)

select
    md5(concat_ws('|', u.vendor, u.source_system, u.source_table, u.raw_id::text)) as spend_line_item_id,
    p.id        as provider_id,
    u.source_system,
    u.source_table,
    u.raw_id,
    u.month_start,
    fc.calendar_quarter,
    extract(year from u.month_start)::integer as calendar_year,
    fc.fiscal_quarter,
    extract(year from u.month_start)::integer + fc.fiscal_year_offset as fiscal_year,
    coalesce(m.bge_alias, u.organization_name) as organization_name,
    coalesce(sm.sub_bge_alias, u.sub_organization_name) as sub_organization_name,
    b.id        as bge_id,
    b.sector_id as sector_id,
    sc.service_category_id,
    sb.id           as sub_bge_id,
    sb.entity_type  as sub_bge_entity_type,
    u.spend_amount
from unioned u
left join {{ ref('fiscal_calendar') }} fc
    on fc.calendar_month = extract(month from u.month_start)::integer
left join {{ source('reference_data', 'service_code') }} sc
    on sc.source_system = u.source_system
    and sc.code = u.lookup_code
left join {{ source('reference_data', 'provider') }} p on p.code = u.vendor
left join {{ ref('bge_alias_map') }} m on m.raw_name = u.organization_name
left join {{ source('reference_data', 'bge') }} b on b.code = coalesce(m.bge_alias, u.organization_name)
left join {{ ref('sub_bge_alias_map') }} sm on sm.raw_name = u.sub_organization_name
left join {{ source('reference_data', 'sub_bge') }} sb on sb.code = coalesce(sm.sub_bge_alias, u.sub_organization_name)
where u.month_start is not null
    and u.spend_amount <> 0
