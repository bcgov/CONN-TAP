{{ config(materialized='view') }}

with normalized as (
    select
        t.raw_id,
        t.ingestion_run_id,
        date_trunc('month', t.statement_date)::date as month_start,
        {{ clean_text('t.sheet_name') }} as organization_name,
        -- account_description is Telus's sub-organization (billing account); resolved to a sub_bge downstream.
        {{ clean_text('t.account_description') }} as sub_organization_name,
        lower({{ clean_text('t.source') }}) as source_service_family,
        lower({{ clean_text('t.statement_category') }}) as statement_category,
        lower({{ clean_text('t.statement_section') }}) as statement_section,
        lower({{ clean_text('t.detail_description') }}) as source_service_description,
        case
            when nullif(trim(t.source_id::text), '') ~ '^-?[0-9]+(\.[0-9]+)?$'
                then (trim(t.source_id::text)::numeric)::bigint::text
            else nullif(trim(t.source_id::text), '')
        end as source_service_id,
        coalesce(t.amount, 0)::numeric(19, 4) as spend_amount
    from {{ source('raw_data', 'raw_telus_spend') }} as t
),

-- Each distinct name is looked up once: match_key is expensive, and calling it per raw row
-- made every query over this view take minutes. Same alias rows per name as a per-row join.
org_map as (
    select n.name, bm.bge_alias
    from (select distinct organization_name as name from normalized) n
    join {{ ref('bge_alias_map') }} bm
        on reference_data.match_key(bm.raw_name) = reference_data.match_key(n.name)
),

sub_map as (
    select n.name, sbm.sub_bge_alias
    from (select distinct sub_organization_name as name from normalized) n
    join (
        select distinct on (reference_data.match_key(raw_name))
               reference_data.match_key(raw_name) as mk, sub_bge_alias
        from {{ ref('sub_bge_alias_map') }}
    ) sbm
        on sbm.mk = reference_data.match_key(n.name)
)

select
    'telus'::text as vendor,
    'ngta'::text as source_system,
    'raw_telus_spend'::text as source_table,
    raw_id,
    ingestion_run_id,
    month_start,
    -- the cleaned tab name itself, for reports that work per tab (rpt_telus_ngta_monthly)
    normalized.organization_name as sheet_name,
    bm.bge_alias as organization_name,
    sbm.sub_bge_alias as sub_organization_name,
    source_service_family,
    source_service_description,
    source_service_id,
    statement_category,
    statement_section,
    'amount'::text as source_amount_name,
    spend_amount
from normalized
left join org_map bm on bm.name = normalized.organization_name
left join sub_map sbm on sbm.name = normalized.sub_organization_name
