{{ config(severity='warn') }}

-- Data-quality guard: every non-null raw sub-BGE / service-designee name coming
-- from the Telus NGTA and Rogers NGTA spend tables must resolve to a sub_bge
-- alias via sub_bge_alias_map. Severity is 'warn' (does not fail the build): a
-- new raw spelling that lacks a seed mapping is surfaced as a warning naming
-- exactly what to add to sub_bge_alias_map.csv. Flip to 'error' above to enforce.
--
-- Scope is intentionally NGTA-only (Telus + Rogers); TSMA sources are covered
-- separately. The raw sub extraction mirrors the `normalized` / `cleaned` CTEs
-- in stg_telus_ngta_spend and stg_rogers_spend -- keep it in sync if a staging
-- raw expression changes.

with src as (
    -- Telus NGTA (all raw_telus_spend rows are NGTA)
    select
        'telus'::text as vendor,
        'raw_telus_spend'::text as source_table,
        nullif(trim(regexp_replace(t.account_description, '[\x00-\x1f\x7f]', '', 'g')), '') as sub_raw
    from {{ source('raw_data', 'raw_telus_spend') }} as t

    union all

    -- Rogers NGTA cellular
    select
        'rogers'::text,
        'raw_rogers_spend_cellular'::text,
        nullif(trim(regexp_replace(c.sub_bge, '[\x00-\x1f\x7f]', '', 'g')), '')
    from {{ source('raw_data', 'raw_rogers_spend_cellular') }} as c
    inner join {{ source('raw_data', 'ingestion_run') }} as r
        on r.ingestion_run_id = c.ingestion_run_id
    where r.provider = 'rogers'

    union all

    -- Rogers NGTA data / voice
    select
        'rogers'::text,
        'raw_rogers_spend_data_voice'::text,
        nullif(trim(regexp_replace(v.sub_bge, '[\x00-\x1f\x7f]', '', 'g')), '')
    from {{ source('raw_data', 'raw_rogers_spend_data_voice') }} as v
    inner join {{ source('raw_data', 'ingestion_run') }} as r
        on r.ingestion_run_id = v.ingestion_run_id
    where r.provider = 'rogers'
)

select distinct
    s.vendor,
    s.source_table,
    s.sub_raw as unmapped_sub_bge_name
from src s
left join {{ ref('sub_bge_alias_map') }} sbm
    on {{ norm_key('sbm.raw_name') }} = {{ norm_key('s.sub_raw') }}
where s.sub_raw is not null
    and sbm.raw_name is null
order by s.vendor, s.source_table, unmapped_sub_bge_name
