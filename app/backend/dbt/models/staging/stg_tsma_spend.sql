{{ config(materialized='view') }}

with cleaned as (

select
    'telus'::text as vendor,
    'tsma'::text as source_system,
    'tsma_wireless'::text as source_table,
    raw_id,
    ingestion_run_id,
    case when ccyymm ~ '^\d{4}(0[1-9]|1[0-2])$' then to_date(ccyymm || '01', 'YYYYMMDD') end
        as month_start,
    coalesce(
        nullif(trim(regexp_replace(lcd_category, '[\x00-\x1f\x7f]', '', 'g')), ''),
        nullif(trim(regexp_replace(lcd_cust_cd,  '[\x00-\x1f\x7f]', '', 'g')), '')
    ) as organization_name,
    null::text as sub_organization_name,
    'wireless'::text as source_service_family,
    lower(nullif(trim(regexp_replace(charge_type, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
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
    'TSMA LITE SCHOOL DISTRICTS'::text as organization_name,
    coalesce(
        nullif(trim(regexp_replace(lcd_category, '[\x00-\x1f\x7f]', '', 'g')), ''),
        nullif(trim(regexp_replace(lcd_cust_cd,  '[\x00-\x1f\x7f]', '', 'g')), '')
    ) as sub_organization_name,
    'wireless'::text as source_service_family,
    lower(nullif(trim(regexp_replace(charge_type, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
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
    coalesce(
        nullif(trim(regexp_replace(entity,      '[\x00-\x1f\x7f]', '', 'g')), ''),
        nullif(trim(regexp_replace(lcd_cust_cd, '[\x00-\x1f\x7f]', '', 'g')), '')
    ) as organization_name,
    null::text as sub_organization_name,
    'wireline'::text as source_service_family,
    lower(nullif(trim(regexp_replace(coalesce(bpi_prod_desc, prod_family_desc, epp3_desc), '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
    nullif(trim(bpi_prod_cd), '') as source_service_id,
    null::text as statement_category,
    lower(nullif(trim(regexp_replace(tsma_service_tower, '[\x00-\x1f\x7f]', '', 'g')), '')) as tsma_service_tower,
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
    'TSMA LITE SCHOOL DISTRICTS'::text as organization_name,
    nullif(trim(regexp_replace(rcid_cust_nm, '[\x00-\x1f\x7f]', '', 'g')), '') as sub_organization_name,
    'wireline'::text as source_service_family,
    lower(nullif(trim(regexp_replace(bpi_prod_desc, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    lower(nullif(trim(regexp_replace(tsma_service_tower, '[\x00-\x1f\x7f]', '', 'g')), '')) as tsma_service_tower,
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
    'Gov BC'::text as organization_name,
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
    nullif(trim(regexp_replace(entity_name, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
    null::text as sub_organization_name,
    'mms'::text as source_service_family,
    'mms'::text as source_service_description,
    null::text as source_service_id,
    null::text as statement_category,
    null::text as tsma_service_tower,
    'total'::text as source_amount_name,
    coalesce(total, 0)::numeric(19, 4) as spend_amount
from {{ source('raw_data', 'tsma_mms') }}

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
    source_service_id,
    statement_category,
    tsma_service_tower,
    source_amount_name,
    spend_amount
-- depends_on: {{ ref('bge_alias_map') }}  -- read by resolve_bge_alias(); do not remove
from cleaned
left join {{ ref('sub_bge_alias_map') }} sbm on reference_data.norm_key(sbm.raw_name) = reference_data.norm_key(cleaned.sub_organization_name)
