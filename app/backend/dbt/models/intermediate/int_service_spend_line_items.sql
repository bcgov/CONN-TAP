{{ config(materialized='view') }}

with telus_excluded_categories as (
    select unnest(array[
        'payment',
        'payments',
        'amount due from last bill',
        'taxes'
    ]::text[]) as statement_category
),

telus_excluded_details as (
    select unnest(array[
        'bc pst',
        'b.c. pst adjustment',
        'bus. services gst',
        'cps gst 100652692',
        'cps gst adjustment 362037',
        'cps pst british columbia 7%',
        'fp gst credit',
        'fp pst credit',
        'gst',
        'gst adj',
        'gst adjustment',
        'gst/hst',
        'gst/hst adjustment',
        'gst tax adjustment',
        'pq pst',
        'pst',
        'pst adjustment',
        'pst-bc',
        'pst-bc adj',
        'pst-mb',
        'pst-qc'
    ]::text[]) as detail_description
),

telus_hardware_details as (
    select unnest(array[
        'hardware purchase charge',
        'device discount repayment',
        'monthly telus easy payment',
        'device discount repay. canc.',
        'device discount repay. - cr',
        'monthly easy payment',
        'telus easy payment balance',
        'equipment adjustment'
    ]::text[]) as detail_description
),

rogers as (
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

telus_ngta as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        organization_name,
        sub_organization_name,
        coalesce(source_service_id, source_service_family) as lookup_code,
        spend_amount
    from {{ ref('stg_telus_ngta_spend') }}
    where (
            source_service_description not in (
                select detail_description from telus_excluded_details
            )
            or source_service_description is null
        )
        and (
            source_service_description in (
                select detail_description from telus_hardware_details
            )
            or coalesce(statement_category, '') not in (
                select statement_category from telus_excluded_categories
            )
        )
),

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
    extract(year from u.month_start)::integer as calendar_year,
    extract(quarter from u.month_start)::integer as calendar_quarter,
    extract(year from u.month_start + interval '9 months')::integer as fiscal_year,
    (((extract(month from u.month_start)::integer + 8) % 12) / 3 + 1)::integer as fiscal_quarter,
    coalesce(m.bge_alias, u.organization_name) as organization_name,
    coalesce(sm.sub_bge_alias, u.sub_organization_name) as sub_organization_name,
    b.id        as bge_id,
    b.sector_id as sector_id,
    sc.service_category_id,
    u.spend_amount
from unioned u
left join {{ source('reference_data', 'service_code') }} sc
    on sc.source_system = u.source_system
    and sc.code = u.lookup_code
left join {{ source('reference_data', 'provider') }} p on p.code = u.vendor
left join {{ ref('bge_alias_map') }} m on m.raw_name = u.organization_name
left join {{ source('reference_data', 'bge') }} b on b.code = coalesce(m.bge_alias, u.organization_name)
left join {{ ref('sub_bge_alias_map') }} sm on sm.raw_name = u.sub_organization_name
where u.month_start is not null
    and sc.service_category_id is not null
    and u.spend_amount <> 0
