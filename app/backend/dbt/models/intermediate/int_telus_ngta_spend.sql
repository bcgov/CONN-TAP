{{ config(materialized='view') }}

-- Applies Telus NGTA-specific exclusion rules so int_service_spend_line_items stays vendor-agnostic.

with source as (
    select * from {{ ref('stg_telus_ngta_spend') }}
),

telus_excluded_categories as (
    select statement_category from {{ ref('telus_excluded_categories') }}
),

telus_excluded_details as (
    select detail_description from {{ ref('telus_excluded_details') }}
),

telus_hardware_details as (
    select detail_description from {{ ref('telus_hardware_details') }}
),

telus_excluded_sections as (
    select statement_section from {{ ref('telus_excluded_sections') }}
),

filtered as (
    select *
    from source
    where
        -- Drop excluded sections (eg: carry-forward balance)
        coalesce(statement_section, '') not in (
            select statement_section from telus_excluded_sections
        )

        -- Drop tax and other explicitly excluded line items
        and (
            source_service_description is null
            or source_service_description not in (select detail_description from telus_excluded_details)
        )

        -- Hardware rows: keep only if wireless family; all other rows: drop excluded categories
        and case
            when source_service_description in (select detail_description from telus_hardware_details)
                then source_service_family = 'wireless'
            else coalesce(statement_category, '') not in (
                select statement_category from telus_excluded_categories
            )
        end
)

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
from filtered
