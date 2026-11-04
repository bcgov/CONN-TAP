{{ config(materialized='view') }}

-- Applies Telus NGTA-specific exclusion rules so int_service_spend_line_items stays vendor-agnostic,
-- then gives each line a category: hardware first, then by matching it to the TELUS pricebooks,
-- then, when nothing matched, the old source rule.

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

-- TELUS's own service codes and their category, for the old rule (step 4).
-- Filtered by provider because Rogers shares the 'ngta' source_system.
source_id_categories as (
    select sc.code, cat.code as service_category_code
    from {{ source('reference_data', 'service_code') }} sc
    join {{ source('reference_data', 'provider') }} p on p.id = sc.provider_id
    join {{ source('reference_data', 'service_category') }} cat on cat.id = sc.service_category_id
    where sc.source_system = 'ngta'
        and p.code = 'telus'
),

-- ============================================================
-- Pricebooks
-- ============================================================

-- Pricebook match by service ID. An ID in more than one pricebook takes the first one (TLS first).
pricebook_ids as (
    select distinct on (service_id)
        service_id,
        service_category_code,
        sub_category_code
    from {{ ref('stg_telus_pricebook_services') }}
    order by service_id, priority
),

-- Pricebook match by rate plan / service / description, when the service ID didn't match.
pricebook_names as (
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
lto_list as (
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

-- ============================================================
-- 2. Hardware: decided before the pricebooks
--    a. source_id 164                         -> cellular hardware
--    b. hardware description on a Wireless line -> cellular hardware
--    c. hardware description on any other line  -> ancillary hardware
-- ============================================================

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

spend_with_hardware as (
    select
        *,
        case
            when source_service_id = '164' then 'cellular_hardware'
            when is_hw and source_service_family = 'wireless' then 'cellular_hardware'
            when is_hw then 'ancillary_hardware'
        end as hardware_category_code
    from flagged
),

-- ============================================================
-- 3. The line's pricebook service ID: the first of these found in the pricebook
--    a. a code written in the description; when there are several, the longest
--    b. the cellular plan name (GoBC V&D ULNA 5GB -> XPULNA5GB)
--    c. the whole cleaned description (TLS IDs are names)
-- ============================================================

code_matches as (
    select distinct on (codes.service_ids)
        codes.service_ids,
        pricebook.service_id
    from (select distinct service_ids from spend_with_hardware) codes
    cross join unnest(codes.service_ids) as code
    join pricebook_ids pricebook on pricebook.service_id = code
    order by codes.service_ids, length(code) desc, code
),

spend_with_service_id as (
    select
        spend.*,
        coalesce(code_match.service_id, plan_match.service_id, description_match.service_id) as pricebook_service_id
    from spend_with_hardware spend
    left join code_matches code_match
        on code_match.service_ids = spend.service_ids
    left join pricebook_ids plan_match
        on plan_match.service_id = {{ telus_cellular_plan_id('spend.source_service_description') }}
    left join pricebook_ids description_match
        on description_match.service_id = spend.cleaned_description
),

-- ============================================================
-- 4. The line's category. Hardware (step 2) comes first.
--    Then TLS: the TLS pricebook, then the LTO list.
--    Then the other pricebooks: by service ID, then by rate plan / service / description.
--    No pricebook match: the old rule (Wireless -> Cellular, then the source_id's category).
-- ============================================================

categorised_spend as (
    select
        spend.*,
        case
            when spend.hardware_category_code is not null then spend.hardware_category_code
            when pricebook.service_category_code = 'time_limited_services' then pricebook.service_category_code
            when lto.service_category_code is not null then lto.service_category_code
            when pricebook.service_category_code is not null then pricebook.service_category_code
            when pricebook_name.service_category_code is not null then pricebook_name.service_category_code

            -- No pricebook match: the old rule
            when spend.source_service_family = 'wireless' then 'cellular'
            when old_rule.service_category_code is not null then old_rule.service_category_code
            -- === TEMPORARY (TODO remove): PHSA Other -> Data, until TELUS confirms the classification ===
            when spend.organization_name = 'PHSA' then 'data'
            else 'unknown'
        end as lookup_code,
        -- The sub-category comes from whichever of the two decided TLS. Hardware has none.
        case
            when spend.hardware_category_code is not null then null
            when pricebook.service_category_code = 'time_limited_services' then pricebook.sub_category_code
            when lto.service_category_code is not null then lto.sub_category_code
        end as sub_category_code
    from spend_with_service_id spend
    left join pricebook_ids pricebook on pricebook.service_id = spend.pricebook_service_id
    left join lto_list lto on lto.charge_description = spend.cleaned_description
    left join pricebook_names pricebook_name on pricebook_name.name = spend.cleaned_description
    left join source_id_categories old_rule on old_rule.code = spend.source_service_id
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
    spend_amount
from categorised_spend
