{{ config(materialized='view') }}

select
    'rogers'::text as vendor,
    'ngta'::text as source_system,
    'raw_rogers_spend_cellular'::text as source_table,
    c.raw_id,
    c.ingestion_run_id,
    date_trunc('month', coalesce(c.invoice_date, r.source_period))::date as month_start,
    nullif(trim(c.bge), '') as organization_name,
    nullif(trim(c.sub_bge), '') as sub_organization_name,
    'cellular'::text as source_service_family,
    nullif(trim(c.plan_description), '') as source_service_description,
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
    nullif(trim(v.bge), '') as organization_name,
    nullif(trim(v.sub_bge), '') as sub_organization_name,
    lower(nullif(trim(v.productline), '')) as source_service_family,
    nullif(trim(coalesce(v.charge_description, v.service_component, v.producttype)), '')
        as source_service_description,
    'billed_amount_pre_tax'::text as source_amount_name,
    coalesce(v.billed_amount_pre_tax, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'raw_rogers_spend_data_voice') }} as v
inner join {{ source('raw_data', 'ingestion_run') }} as r
    on r.ingestion_run_id = v.ingestion_run_id
where r.provider = 'rogers'
