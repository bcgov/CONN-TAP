{{ config(materialized='view') }}

with normalized as (
    select
        t.raw_id,
        t.ingestion_run_id,
        date_trunc('month', t.statement_date)::date as month_start,
        nullif(trim(regexp_replace(t.sheet_name, '[\x00-\x1f\x7f]', '', 'g')), '') as organization_name,
        lower(nullif(trim(regexp_replace(t.source, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_family,
        lower(nullif(trim(regexp_replace(t.statement_category, '[\x00-\x1f\x7f]', '', 'g')), '')) as statement_category,
        lower(nullif(trim(regexp_replace(t.detail_description, '[\x00-\x1f\x7f]', '', 'g')), '')) as source_service_description,
        case
            when nullif(trim(t.source_id::text), '') ~ '^-?[0-9]+(\.[0-9]+)?$'
                then (trim(t.source_id::text)::numeric)::bigint::text
            else nullif(trim(t.source_id::text), '')
        end as source_service_id,
        coalesce(t.amount, 0)::numeric(19, 4) as spend_amount
    from {{ source('raw_data', 'raw_telus_spend') }} as t
)

select
    'telus'::text as vendor,
    'ngta'::text as source_system,
    'raw_telus_spend'::text as source_table,
    raw_id,
    ingestion_run_id,
    month_start,
    organization_name,
    null::text as sub_organization_name,
    source_service_family,
    source_service_description,
    source_service_id,
    statement_category,
    'amount'::text as source_amount_name,
    spend_amount
from normalized
