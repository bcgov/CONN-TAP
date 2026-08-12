{{ config(materialized='view') }}

with cleaned as (

select
    'rogers'::text as vendor,
    'ngta'::text as source_system,
    'raw_rogers_spend_cellular'::text as source_table,
    c.raw_id,
    c.ingestion_run_id,
    (date_trunc('month', coalesce(c.invoice_date, r.source_period)) - interval '1 month')::date as month_start,
    nullif(trim(regexp_replace(c.bge, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
    nullif(trim(regexp_replace(c.sub_bge, '[\x00-\x1f\x7f]', '', 'g')), '') as sub_organization_name,
    'cellular'::text as source_service_family,
    lower(nullif(trim(regexp_replace(c.plan_description, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
    'billed_amount_pre_tax'::text as source_amount_name,
    coalesce(c.billed_amount_pre_tax, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'raw_rogers_spend_cellular') }} as c
inner join {{ source('raw_data', 'ingestion_run') }} as r
    on r.ingestion_run_id = c.ingestion_run_id
where r.provider = 'rogers'

union all

select
    'rogers'::text as vendor,
    'ngta'::text as source_system,
    'raw_rogers_spend_data_voice'::text as source_table,
    v.raw_id,
    v.ingestion_run_id,
    date_trunc('month', coalesce(v.billingdate, r.source_period))::date as month_start,
    nullif(trim(regexp_replace(v.bge, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
    nullif(trim(regexp_replace(v.sub_bge, '[\x00-\x1f\x7f]', '', 'g')), '') as sub_organization_name,
    coalesce(lower(nullif(trim(regexp_replace(v.productline, '[\x00-\x1f\x7f]', '', 'g')), '')), 'other') as source_service_family,
    lower(nullif(trim(regexp_replace(coalesce(v.charge_description, v.service_component, v.producttype), '[\x00-\x1f\x7f]', '', 'g')), ''))
        as source_service_description,
    'billed_amount_pre_tax'::text as source_amount_name,
    coalesce(v.billed_amount_pre_tax, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'raw_rogers_spend_data_voice') }} as v
inner join {{ source('raw_data', 'ingestion_run') }} as r
    on r.ingestion_run_id = v.ingestion_run_id
where r.provider = 'rogers'

)

select
    vendor,
    source_system,
    source_table,
    raw_id,
    ingestion_run_id,
    month_start,
    reference_data.resolve_bge_alias(cleaned.organization_name) as organization_name,
    sbm.sub_bge_alias as sub_organization_name,
    source_service_family,
    source_service_description,
    source_amount_name,
    spend_amount
-- depends_on: {{ ref('bge_alias_map') }}  -- read by resolve_bge_alias(); do not remove
from cleaned
left join {{ ref('sub_bge_alias_map') }} sbm on reference_data.norm_key(sbm.raw_name) = reference_data.norm_key(cleaned.sub_organization_name)
