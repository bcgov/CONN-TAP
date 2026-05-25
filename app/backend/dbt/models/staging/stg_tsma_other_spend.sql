{{ config(materialized='view') }}

select
    'telus'::text as vendor,
    'tsma_other'::text as source_system,
    'tsma_other_managed_security'::text as source_table,
    raw_id,
    ingestion_run_id,
    date_trunc('month', month_start_dt)::date as month_start,
    nullif(trim(rcid_cust_nm), '') as organization_name,
    null::text as sub_organization_name,
    'managed_security'::text as source_service_family,
    nullif(trim(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc)), '') as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    nullif(trim(tsma_service_tower), '') as tsma_service_tower,
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
    nullif(trim(rcid_cust_nm), '') as organization_name,
    null::text as sub_organization_name,
    'managed_router'::text as source_service_family,
    nullif(trim(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc)), '') as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    nullif(trim(tsma_service_tower), '') as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_other_managed_router') }}
