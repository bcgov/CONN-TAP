{{ config(severity='error') }}

-- Data-quality guard: every non-null raw sub-org name coming from the TSMA Lite
-- wireless and wireline spend tables must resolve to a sub_bge alias via
-- sub_bge_alias_map. Severity is 'error': the build fails and names exactly
-- what to add to sub_bge_alias_map.csv.
--
-- Scope is TSMA Lite only, the gap left by assert_ngta_sub_bge_names_mapped_to_alias
-- (which is NGTA-only). The raw sub extraction mirrors the tsma_lite_wireless /
-- tsma_lite_wireline CTEs in stg_tsma_spend -- keep it in sync if a staging raw
-- expression changes.

with src as (
    select
        'tsma_lite_wireless'::text as source_table,
        nullif(trim(regexp_replace(w.rcid_cust_nm, '[\x00-\x1f\x7f]', '', 'g')), '') as sub_raw
    from {{ source('raw_data', 'tsma_lite_wireless') }} as w

    union all

    select
        'tsma_lite_wireline'::text,
        nullif(trim(regexp_replace(l.rcid_cust_nm, '[\x00-\x1f\x7f]', '', 'g')), '')
    from {{ source('raw_data', 'tsma_lite_wireline') }} as l
)

select distinct
    s.source_table,
    s.sub_raw as unmapped_sub_bge_name
from src s
left join {{ ref('sub_bge_alias_map') }} sbm
    on reference_data.match_key(sbm.raw_name) = reference_data.match_key(s.sub_raw)
where s.sub_raw is not null
    and sbm.raw_name is null
order by s.source_table, unmapped_sub_bge_name
