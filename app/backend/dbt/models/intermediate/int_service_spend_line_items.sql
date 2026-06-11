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
        case
            when source_service_family = 'cellular' then 'Cellular'
            when source_service_family = 'data' then 'Data'
            when source_service_family = 'voice' then 'Voice'
        end as service_category,
        spend_amount
    from {{ ref('stg_rogers_spend') }}
),

telus_ngta as (
    select
        t.vendor,
        t.source_system,
        t.source_table,
        t.raw_id,
        t.month_start,
        t.organization_name,
        t.sub_organization_name,
        coalesce(
            case when t.source_service_family = 'wireless' then 'Cellular' end,
            sid.service_category
        ) as service_category,
        t.spend_amount
    from {{ ref('stg_telus_ngta_spend') }} t
    left join {{ source('reference_data', 'service_id') }} sid
        on sid.source_system = 'ngta'
        and sid.code         = t.source_service_id
    where (
            t.source_service_description not in (
                select detail_description from telus_excluded_details
            )
            or t.source_service_description is null
        )
        and (
            t.source_service_description in (
                select detail_description from telus_hardware_details
            )
            or coalesce(t.statement_category, '') not in (
                select statement_category from telus_excluded_categories
            )
        )
),

tsma as (
    select
        t.vendor,
        t.source_system,
        t.source_table,
        t.raw_id,
        t.month_start,
        t.organization_name,
        t.sub_organization_name,
        coalesce(
            case
                when t.source_service_family = 'wireless' then 'Cellular'
                when t.source_service_family in ('ivr', 'mms') then 'Temporary Services'
            end,
            st.service_category
        ) as service_category,
        t.spend_amount
    from {{ ref('stg_tsma_spend') }} t
    left join {{ source('reference_data', 'service_tower') }} st
        on st.source_system = 'tsma'
        and st.code         = t.tsma_service_tower
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
        'Other Professional Services'::text as service_category,
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
    md5(concat_ws('|', vendor, source_system, source_table, raw_id::text)) as spend_line_item_id,
    p.id        as provider_id,
    source_system,
    source_table,
    raw_id,
    month_start,
    extract(year from month_start)::integer as calendar_year,
    extract(quarter from month_start)::integer as calendar_quarter,
    extract(year from month_start + interval '9 months')::integer as fiscal_year,
    (((extract(month from month_start)::integer + 8) % 12) / 3 + 1)::integer as fiscal_quarter,
    coalesce(m.bge_alias, u.organization_name) as organization_name,
    coalesce(sm.sub_bge_alias, u.sub_organization_name) as sub_organization_name,
    b.id        as bge_id,
    b.sector_id as sector_id,
    service_category,
    spend_amount
from unioned u
left join {{ source('reference_data', 'provider') }} p on p.code = u.vendor
left join {{ ref('bge_alias_map') }} m on m.raw_name = u.organization_name
left join {{ source('reference_data', 'bge') }} b on b.code = coalesce(m.bge_alias, u.organization_name)
left join {{ ref('sub_bge_alias_map') }} sm on sm.raw_name = u.sub_organization_name
where month_start is not null
    and service_category is not null
    and spend_amount <> 0
