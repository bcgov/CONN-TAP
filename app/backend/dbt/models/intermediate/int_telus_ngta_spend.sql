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
        month_start is not null

        -- Drop excluded sections (eg: carry-forward balance)
        and coalesce(statement_section, '') not in (
            select statement_section from telus_excluded_sections
        )

        -- Drop tax and other explicitly excluded line items
        and (
            source_service_description is null
            or source_service_description not in (select detail_description from telus_excluded_details)
        )

        -- Category exclusions apply even to hardware descriptions and source_id 164.
        and coalesce(statement_category, '') not in (
            select statement_category from telus_excluded_categories
        )
),

flagged as (
    select
        s.*,
        -- telus_hardware_details entries are LIKE patterns ('%' = variable suffix)
        exists (
            select 1 from telus_hardware_details h
            where s.source_service_description like h.detail_description
        ) as is_hw
    from filtered s
)

select
    vendor,
    source_system,
    source_table,
    raw_id,
    month_start,
    organization_name,
    sub_organization_name,
    -- Hardware rows resolve through 164 (Cellular Hardware) whatever their own
    -- source_id, matching the cellular_hardware bucket in scripts/sql/telus.sql.
    case
        when is_hw then '164'
        else coalesce(source_service_id, source_service_family)
    end as lookup_code,
    spend_amount
from flagged
-- 'onetime' alone also covers non-cellular charges. Hardware descriptions
-- require Wireless or the confirmed cellular equipment source_id 164.
where not is_hw or source_service_family = 'wireless' or source_service_id = '164'
