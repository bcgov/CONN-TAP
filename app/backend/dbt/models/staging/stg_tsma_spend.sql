{{ config(materialized='view') }}

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_wireless'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(lcd_category), '') as organization_name,
    null::text as sub_organization_name,
    'wireless'::text as source_service_family,
    nullif(trim(charge_type), '') as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    null::text as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_wireless') }}

union all

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_lite_wireless'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(lcd_category), '') as organization_name,
    null::text as sub_organization_name,
    'wireless'::text as source_service_family,
    nullif(trim(charge_type), '') as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    null::text as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_lite_wireless') }}

union all

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_wireline'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(entity), '') as organization_name,
    null::text as sub_organization_name,
    'wireline'::text as source_service_family,
    nullif(trim(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc)), '') as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    nullif(trim(tsma_service_tower), '') as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_wireline') }}

union all

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_lite_wireline'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(rcid_cust_nm), '') as organization_name,
    null::text as sub_organization_name,
    'wireline'::text as source_service_family,
    nullif(trim(bpi_prod_desc), '') as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    nullif(trim(tsma_service_tower), '') as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_lite_wireline') }}

union all

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_ivr'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(rcid_cust_nm), '') as organization_name,
    null::text as sub_organization_name,
    'ivr'::text as source_service_family,
    'voice ivr'::text as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    null::text as tsma_service_tower,
    'billed_amt'::text as source_amount_name,
    coalesce(billed_amt, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_ivr') }}

union all

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_mms'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    nullif(trim(entity_name), '') as organization_name,
    null::text as sub_organization_name,
    'mms'::text as source_service_family,
    'mms'::text as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    null::text as tsma_service_tower,
    'total'::text as source_amount_name,
    coalesce(total, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_mms') }}
