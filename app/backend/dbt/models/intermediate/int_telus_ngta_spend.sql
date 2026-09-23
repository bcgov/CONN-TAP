{{ config(materialized='view') }}

-- Applies Telus NGTA-specific exclusion rules so int_service_spend_line_items stays vendor-agnostic.

with source as (
    select
        *,
        -- Hardware is matched on the description's word signature, not its literal
        reference_data.telus_detail_signature(source_service_description) as detail_signature
    from {{ ref('stg_telus_ngta_spend') }}
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

flagged_hardware_in_detailed_description as (
    select
        *,
        detail_signature in (select detail_description from telus_hardware_details) as is_hardware
    from source
),

filtered as (
    select *
    from flagged_hardware_in_detailed_description
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

        -- Hardware rows: keep only if wireless-plan-sourced or explicitly source_id 164
        -- (the confirmed cellular one-time equipment code); all other rows: drop excluded
        -- categories. 'onetime' isn't a safe signal by itself -- it covers non-cellular
        -- one-time charges too, so it isn't accepted here on its own.
        and case
            when is_hardware
                then source_service_family = 'wireless' or source_service_id = '164'
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
    -- setting 164 as the lookup code for hardware rows
    case
        when is_hardware then '164'
        else coalesce(source_service_id, source_service_family)
    end as lookup_code,
    spend_amount
from filtered
