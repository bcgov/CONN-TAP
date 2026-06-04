{{ config(materialized='view') }}

with telus_excluded_categories as (
    select unnest(array[
        'Payment',
        'Payments',
        'Amount due from last bill',
        'Amount Due from last bill',
        'Taxes'
    ]::text[]) as statement_category
),

telus_excluded_details as (
    select unnest(array[
        'BC PST',
        'B.C. PST Adjustment',
        'BUS. SERVICES GST',
        'CPS GST 100652692',
        'CPS GST ADJUSTMENT 362037',
        'CPS PST BRITISH COLUMBIA 7%',
        'FP GST Credit',
        'FP PST Credit',
        'GST',
        'GST adj',
        'GST ADJUSTMENT',
        'GST/HST',
        'GST/HST ADJUSTMENT',
        'GST Tax Adjustment',
        'PQ PST',
        'PST',
        'PST ADJUSTMENT',
        'PST-BC',
        'PST-BC adj',
        'PST-MB',
        'PST-QC'
    ]::text[]) as detail_description
),

telus_hardware_details as (
    select unnest(array[
        'Hardware Purchase Charge',
        'Device Discount Repayment',
        'Monthly TELUS Easy Payment',
        'Device discount repay. canc.',
        'Device discount repay. - CR',
        'Monthly Easy Payment',
        'TELUS Easy Payment Balance',
        'Equipment Adjustment'
    ]::text[]) as detail_description
),

rogers as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        case
            when source_service_family = 'cellular' then 'Cellular'
            when source_service_family = 'data' then 'Data'
            when source_service_family = 'voice' then 'Voice'
        end as service_category,
        spend_amount
    from {{ ref('stg_rogers_spend') }}
),

telus_ngta as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        case
            when source_service_family = 'wireless' or source_service_id in ('164', '130') then 'Cellular'
            when source_service_id in ('1001', '103') then 'Data'
            when source_service_id in ('104', '102', '106') then 'Voice'
        end as service_category,
        spend_amount
    from {{ ref('stg_telus_ngta_spend') }}
    where (
            source_service_description not in (
                select detail_description from telus_excluded_details
            )
            or source_service_description is null
        )
        and (
            source_service_description in (
                select detail_description from telus_hardware_details
            )
            or coalesce(statement_category, '') not in (
                select statement_category from telus_excluded_categories
            )
        )
),

tsma as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        case
            when source_service_family = 'wireless' then 'Cellular'
            when tsma_service_tower in ('Business Internet', 'Data - WAN') then 'Data'
            when tsma_service_tower in ('Conferencing', 'Long Distance', 'Voice') then 'Voice'
            when tsma_service_tower = 'Managed WLAN' then 'Other Professional Services'
            when source_service_family in ('ivr', 'mms') then 'Temporary Services'
        end as service_category,
        spend_amount
    from {{ ref('stg_tsma_spend') }}
),

tsma_other as (
    select
        vendor,
        source_system,
        source_table,
        raw_id,
        month_start,
        'Other Professional Services'::text as service_category,
        spend_amount
    from {{ ref('stg_tsma_other_spend') }}
),

unioned as (
    select * from rogers
    union all
    select * from telus_ngta
    union all
    select * from tsma
    union all
    select * from tsma_other
)

select
    md5(concat_ws('|', vendor, source_system, source_table, raw_id::text)) as spend_line_item_id,
    vendor,
    source_system,
    source_table,
    raw_id,
    month_start,
    extract(year from month_start)::integer as calendar_year,
    extract(quarter from month_start)::integer as calendar_quarter,
    extract(year from month_start + interval '9 months')::integer as fiscal_year,
    (((extract(month from month_start)::integer + 8) % 12) / 3 + 1)::integer as fiscal_quarter,
    service_category,
    spend_amount
from unioned
where month_start is not null
    and service_category is not null
    and spend_amount <> 0
