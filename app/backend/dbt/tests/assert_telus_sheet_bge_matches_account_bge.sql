{{ config(severity='error') }}

-- Cross-check for TELUS NGTA ownership: the BGE implied by the workbook tab
-- (sheet_name -> bge_alias_map) should be the same BGE the account resolves to
-- (account_description -> sub_bge_alias_map -> sub_bge's parent BGE).
-- int_service_spend_line_items takes the account's parent BGE when there is one,
-- so every row here is spend that dbt books under a different BGE than its tab.
--
-- Severity is 'error': the build fails until each tab / account pair is
-- resolved, either a sub_bge_alias_map entry pointing at the wrong sub_bge, or
-- an account TELUS filed under another BGE's tab.
--
-- ECC is a ministry under Gov BC, not a BGE: an ECC tab is compared as Gov BC,
-- matching the rewrite in int_service_spend_line_items. Accounts that don't
-- resolve to a sub_bge are skipped (the tab's BGE is used for them).
--
-- Resolution mirrors stg_telus_ngta_spend (clean_text, then match_key joins to
-- the alias maps), but runs on distinct tab / account pairs rather than per raw
-- row, so it stays fast enough for the deploy hook. It reads raw rows before the
-- tax / payment exclusions, so its amounts can be slightly higher than the fact's.
--
-- scripts/validation/telus/checks/14_sheet_mapping_issues.sql runs the same rule in the
-- TELUS validation report ('Account BGE differs') -- keep the two in sync.

with raw_pairs as (
    select
        t.sheet_name,
        t.account_description,
        count(*)      as row_count,
        sum(t.amount) as amount
    from {{ source('raw_data', 'raw_telus_spend') }} as t
    group by 1, 2
),

pairs as (
    select
        {{ clean_text('r.sheet_name') }}          as sheet_name,
        {{ clean_text('r.account_description') }} as account_description,
        sum(r.row_count)                          as row_count,
        sum(r.amount)                             as amount
    from raw_pairs r
    group by 1, 2
),

sub_map as (
    select distinct on (reference_data.match_key(raw_name))
           reference_data.match_key(raw_name) as mk, sub_bge_alias
    from {{ ref('sub_bge_alias_map') }}
)

select
    p.sheet_name,
    tb.code              as tab_bge,
    p.account_description,
    sb.code              as account_sub_bge,
    ab.code              as account_bge,
    sum(p.row_count)     as row_count,
    sum(p.amount)        as amount
from pairs p
left join {{ ref('bge_alias_map') }} bm
    on reference_data.match_key(bm.raw_name) = reference_data.match_key(p.sheet_name)
left join {{ source('reference_data', 'bge') }} tb
    on reference_data.norm_key(tb.code) = reference_data.norm_key(
           case when bm.bge_alias = 'ECC' then 'Gov BC' else bm.bge_alias end)
join sub_map sm
    on sm.mk = reference_data.match_key(p.account_description)
join {{ source('reference_data', 'sub_bge') }} sb
    on reference_data.norm_key(sb.code) = reference_data.norm_key(sm.sub_bge_alias)
join {{ source('reference_data', 'bge') }} ab
    on ab.id = sb.bge_id
where ab.id is distinct from tb.id
group by 1, 2, 3, 4, 5
order by 1, 3
