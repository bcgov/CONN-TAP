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

pricebook as (
    select * from {{ ref('stg_telus_pricebook_services') }}
),

-- Analysts' list of TLS charge descriptions/LTO list, this will be provided when there are more entries to include.
-- Matched exactly once the bill's trailing '*' is stripped (the list itself has no '*'):
tls_charges as (
    select
        upper(charge_description) as charge_description,
        'time_limited_services'::text as service_category_code,
        sub_category_code
    from {{ ref('telus_tls_charge_descriptions') }}
),

{# Not used now: needed by the old source_id rule below.
-- TELUS's own service codes. Filtered by provider because Rogers shares the
-- 'ngta' source_system.
telus_service_codes as (
    select sc.code
    from {{ source('reference_data', 'service_code') }} sc
    join {{ source('reference_data', 'provider') }} p on p.id = sc.provider_id
    where sc.source_system = 'ngta'
        and p.code = 'telus'
),
#}

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
    -- TLS comes first: the TLS pricebook, then the analysts' TLS list, then the other pricebooks.
    case
        when pb.service_category_code = 'time_limited_services' then pb.service_category_code
        when tls.service_category_code is not null then tls.service_category_code
        else coalesce(pb.service_category_code, 'unknown')
    end as lookup_code,
    -- The sub-category comes from whichever of the two decided TLS.
    case
        when pb.service_category_code = 'time_limited_services' then pb.sub_category_code
        when tls.service_category_code is not null then tls.sub_category_code
    end as sub_category_code,
    {# Old source_id rule, not used now.
    -- Same precedence as the spend report: hardware first, then Wireless
    -- (Cellular Plans) whatever its source_id, then a confirmed source_id.
    -- A blank or unconfirmed source_id is the report's Other: telus_other (Unknown).
    case
        when is_hw or source_service_id = '164' then '164'
        when source_service_family = 'wireless' then 'wireless'
        when source_service_id in (select code from telus_service_codes) then source_service_id
        -- === TEMPORARY (TODO remove): PHSA Other → Data ===
        -- Until upstream classification is fixed, PHSA spend that would be Other
        -- (telus_other) is booked as Data via 103 (Wireline Data). The only copy of this
        -- rule: the spend report, the validation report and the dashboards all read it.
        when organization_name = 'PHSA' then '103'
        -- === END TEMPORARY PHSA Other → Data ===
        else 'telus_other'
    end as lookup_code,
    #}
    spend_amount
from flagged
left join pricebook pb on pb.service_id_key = flagged.pricebook_service_id
left join tls_charges tls on tls.charge_description = upper({{ clean_text('flagged.source_service_description', strip_star=true) }})
-- 'onetime' alone also covers non-cellular charges. Hardware descriptions
-- require Wireless or the confirmed cellular equipment source_id 164.
where not is_hw or source_service_family = 'wireless' or source_service_id = '164'
