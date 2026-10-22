{{ config(materialized='view') }}

-- Applies Telus NGTA-specific exclusion rules so int_service_spend_line_items stays vendor-agnostic.

with source as (
    select * from {{ ref('stg_telus_ngta_spend') }}
),

telus_excluded_categories as (
    select statement_category from {{ ref('telus_excluded_categories') }}
),

telus_excluded_details as (
    select {{ text_key('detail_description') }} as detail_key from {{ ref('telus_excluded_details') }}
),

telus_hardware_details as (
    select {{ text_key('detail_description') }} as detail_key from {{ ref('telus_hardware_details') }}
),

telus_excluded_sections as (
    select statement_section from {{ ref('telus_excluded_sections') }}
),

-- TELUS's own service codes. Filtered by provider because Rogers shares the
-- 'ngta' source_system.
telus_service_codes as (
    select sc.code
    from {{ source('reference_data', 'service_code') }} sc
    join {{ source('reference_data', 'provider') }} p on p.id = sc.provider_id
    where sc.source_system = 'ngta'
        and p.code = 'telus'
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
            or {{ text_key('source_service_description') }} not in (select detail_key from telus_excluded_details)
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
            where {{ text_key('s.source_service_description') }} like h.detail_key
        ) as is_hw
    from filtered s
)

select
    vendor,
    source_system,
    source_table,
    raw_id,
    month_start,
    sheet_name,
    organization_name,
    sub_organization_name,
    -- Same precedence as the spend report: hardware first, then Wireless
    -- (Cellular Plans) whatever its source_id, then a confirmed source_id.
    -- A blank or unconfirmed source_id is the report's Other: telus_other (Unknown).
    case
        when is_hw or source_service_id = '164' then '164'
        when source_service_family = 'wireless' then 'wireless'
        when source_service_id in (select code from telus_service_codes) then source_service_id
        -- === TEMPORARY (TODO remove): PHSA Other → Data ===
        -- Mirrors the override in scripts/telus_ngta.py. Until upstream
        -- classification is fixed, PHSA spend that would be Other (telus_other)
        -- is booked as Data via 103 (Wireline Data). The validation report reads this
        -- model, so it follows automatically; remove this and the Python copy together.
        when organization_name = 'PHSA' then '103'
        -- === END TEMPORARY PHSA Other → Data ===
        else 'telus_other'
    end as lookup_code,
    spend_amount
from flagged
-- 'onetime' alone also covers non-cellular charges. Hardware descriptions
-- require Wireless or the confirmed cellular equipment source_id 164.
where not is_hw or source_service_family = 'wireless' or source_service_id = '164'
