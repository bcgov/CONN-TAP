{{ config(materialized='view') }}

-- Applies Telus NGTA-specific exclusion rules so int_service_spend_line_items stays vendor-agnostic,
-- then gives each line a category by matching it to the TELUS pricebooks.

with source as (
    select * from {{ ref('stg_telus_ngta_spend') }}
),

-- ============================================================
-- Exclusion lists
-- ============================================================

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

-- ============================================================
-- Pricebooks
-- ============================================================

-- Pricebook match by service ID. An ID in more than one pricebook takes the first one (TLS first).
telus_pricebook_service_ids_from_pricebook as (
    select distinct on (service_id)
        service_id,
        service_category_code,
        sub_category_code
    from {{ ref('stg_telus_pricebook_services') }}
    order by service_id, priority
),

-- Pricebook match by rate plan / service / description, when the service ID didn't match.
telus_pricebook_other_matchers_from_pricebook as (
    select distinct on (name)
        name,
        service_category_code
    from (
        select rate_plan as name, service_category_code, priority from {{ ref('stg_telus_pricebook_services') }}
        union all
        select service, service_category_code, priority from {{ ref('stg_telus_pricebook_services') }}
        union all
        select description, service_category_code, priority from {{ ref('stg_telus_pricebook_services') }}
    ) names
    where name is not null
    order by name, priority
),

-- Analysts' list of TLS charge descriptions/LTO list, this will be provided when there are more entries to include.
-- Matched exactly, both sides cleaned the same way (punctuation and the bill's trailing '*' ignored):
tls_charges as (
    select
        upper({{ clean_text('charge_description', strip_punctuation=true) }}) as charge_description,
        'time_limited_services'::text as service_category_code,
        sub_category_code
    from {{ ref('telus_tls_charge_descriptions') }}
),

-- ============================================================
-- 1. Exclusions: the lines that are kept
-- ============================================================

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
),

kept_spend as (
    select *
    from flagged
    -- 'onetime' alone also covers non-cellular charges. Hardware descriptions
    -- require Wireless or the confirmed cellular equipment source_id 164.
    where not is_hw or source_service_family = 'wireless' or source_service_id = '164'
),

-- ============================================================
-- 2. The line's pricebook service ID: the first of these found in the pricebook
--    a. a code written in the description; when there are several, the longest
--    b. the cellular plan name (GoBC V&D ULNA 5GB -> XPULNA5GB)
--    c. the whole cleaned description (TLS IDs are names)
-- ============================================================

code_matches as (
    select distinct on (codes.service_ids)
        codes.service_ids,
        pb.service_id
    from (select distinct service_ids from kept_spend) codes
    cross join unnest(codes.service_ids) as code
    join telus_pricebook_service_ids_from_pricebook pb on pb.service_id = code
    order by codes.service_ids, length(code) desc, code
),

spend_with_service_id as (
    select
        kept_spend.*,
        coalesce(code_match.service_id, plan_match.service_id, description_match.service_id) as pricebook_service_id
    from kept_spend
    left join code_matches code_match
        on code_match.service_ids = kept_spend.service_ids
    left join telus_pricebook_service_ids_from_pricebook plan_match
        on plan_match.service_id = {{ telus_cellular_plan_id('kept_spend.source_service_description') }}
    left join telus_pricebook_service_ids_from_pricebook description_match
        on description_match.service_id = kept_spend.cleaned_description
),

-- ============================================================
-- 3. The line's category. TLS comes first: the TLS pricebook, then the LTO list.
--    Then the other pricebooks: by service ID, then by rate plan / service / description.
-- ============================================================

categorised_spend as (
    select
        spend.*,
        case
            when pb.service_category_code = 'time_limited_services' then pb.service_category_code
            when tls.service_category_code is not null then tls.service_category_code
            else coalesce(pb.service_category_code, names.service_category_code, 'unknown')
        end as lookup_code,
        -- The sub-category comes from whichever of the two decided TLS.
        case
            when pb.service_category_code = 'time_limited_services' then pb.sub_category_code
            when tls.service_category_code is not null then tls.sub_category_code
        end as sub_category_code
    from spend_with_service_id spend
    left join telus_pricebook_service_ids_from_pricebook pb on pb.service_id = spend.pricebook_service_id
    left join tls_charges tls on tls.charge_description = spend.cleaned_description
    left join telus_pricebook_other_matchers_from_pricebook names on names.name = spend.cleaned_description
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
    lookup_code,
    sub_category_code,
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
from categorised_spend
