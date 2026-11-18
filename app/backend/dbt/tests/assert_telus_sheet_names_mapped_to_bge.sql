{{ config(severity='error') }}

-- Gate: every TELUS NGTA sheet (tab) name must resolve to a BGE through
-- bge_alias_map. A tab is a BGE, so an unrecognised tab means spend with no
-- owner. Severity is 'error': the build fails and names exactly what to add to
-- bge_alias_map.csv.
--
-- The match mirrors stg_telus_ngta_spend exactly (the clean_text macro, then
-- reference_data.match_key equality), so this reports precisely
-- the tabs the pipeline would leave without a BGE. A blank tab name shows as null.
-- That every alias targets a real BGE (or the intentional ECC) is checked by the
-- relationships test on bge_alias_map in seeds/_seeds.yml.
--
-- Raw rows are grouped by tab name first, so cleaning and match_key run once per
-- distinct name rather than once per raw row (match_key per row over the full
-- table is what made the disabled NGTA sub-BGE test take ~17 minutes).
--
-- scripts/validation/telus/checks/14_sheet_mapping_issues.sql runs the same rule in the
-- TELUS validation report ('Unmapped sheet') -- keep the two in sync.

with raw_sheets as (
    select
        t.sheet_name,
        min(date_trunc('month', t.statement_date))::date as first_month,
        max(date_trunc('month', t.statement_date))::date as last_month,
        count(*)                                         as row_count,
        sum(t.amount)                                    as amount
    from {{ source('raw_data', 'raw_telus_spend') }} as t
    group by t.sheet_name
),

sheets as (
    select
        {{ clean_text('r.sheet_name') }} as sheet_name,
        min(r.first_month)               as first_month,
        max(r.last_month)                as last_month,
        sum(r.row_count)                 as row_count,
        sum(r.amount)                    as amount
    from raw_sheets r
    group by 1
)

select
    s.sheet_name as unmapped_sheet_name,
    s.first_month,
    s.last_month,
    s.row_count,
    s.amount
from sheets s
left join {{ ref('bge_alias_map') }} bm
    on reference_data.match_key(bm.raw_name) = reference_data.match_key(s.sheet_name)
where bm.raw_name is null
order by 1
