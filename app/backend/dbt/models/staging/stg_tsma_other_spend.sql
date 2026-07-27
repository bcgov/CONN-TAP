{{ config(materialized='view') }}

with cleaned as (

select
    'telus'::text as vendor,
    'tsma_other'::text as source_system,
    'tsma_other_managed_security'::text as source_table,
    raw_id,
    ingestion_run_id,
    date_trunc('month', month_start_dt)::date as month_start,
    nullif(trim(regexp_replace(lcd_cust_cd, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
    null::text as sub_organization_name,
    'managed_security'::text as source_service_family,
    lower(nullif(trim(regexp_replace(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc), '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    lower(nullif(trim(regexp_replace(tsma_service_tower, '[\x00-\x1f\x7f]', '', 'g')), '')) as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_other_managed_security') }}

union all

select
    'telus'::text as vendor,
    'tsma_other'::text as source_system,
    'tsma_other_managed_router'::text as source_table,
    raw_id,
    ingestion_run_id,
    date_trunc('month', month_start_dt)::date as month_start,
    nullif(trim(regexp_replace(lcd_cust_cd, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
    null::text as sub_organization_name,
    'managed_router'::text as source_service_family,
    lower(nullif(trim(regexp_replace(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc), '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    lower(nullif(trim(regexp_replace(tsma_service_tower, '[\x00-\x1f\x7f]', '', 'g')), '')) as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_other_managed_router') }}

)

select
    vendor,
    source_system,
    source_table,
    raw_id,
    ingestion_run_id,
    month_start,
    bm.bge_alias as organization_name,
    sbm.sub_bge_alias as sub_organization_name,
    source_service_family,
    source_service_description,
    source_service_id,
    statement_category,
    tsma_service_tower,
    source_amount_name,
    spend_amount
from cleaned
left join {{ ref('bge_alias_map') }} bm on {{ norm_key('bm.raw_name') }} = {{ norm_key('cleaned.organization_name') }}
left join {{ ref('sub_bge_alias_map') }} sbm on {{ norm_key('sbm.raw_name') }} = {{ norm_key('cleaned.sub_organization_name') }}
