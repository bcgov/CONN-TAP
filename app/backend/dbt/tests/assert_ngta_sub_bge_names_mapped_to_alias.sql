{{ config(severity='warn') }}

-- Data-quality guard: every non-null raw sub-BGE / service-designee name coming
-- from the Telus NGTA and Rogers NGTA spend tables must resolve to a sub_bge
-- alias via sub_bge_alias_map, matched on reference_data.match_key -- the same
-- key the staging models join on, so this reports exactly what the pipeline
-- would fail to resolve. Severity is 'error' (2026-10-15): a new raw spelling
-- that lacks a seed mapping fails the build, naming exactly what to add to
-- sub_bge_alias_map.csv.
--
-- Scope is intentionally NGTA-only (Telus + Rogers); TSMA sources are covered
-- separately. The raw sub extraction mirrors the `normalized` / `cleaned` CTEs
-- in stg_telus_ngta_spend and stg_rogers_spend -- keep it in sync if a staging
-- raw expression changes.
--
-- Each source is reduced to its distinct raw names first, so cleaning and
-- match_key run once per name instead of once per raw row (per-row match_key took
-- ~17 min on deploy; this form runs in seconds and returns the same rows).

with raw_names as (
    -- Telus NGTA (all raw_telus_spend rows are NGTA)
    select 'telus'::text as vendor, 'raw_telus_spend'::text as source_table, t.account_description as raw_name
    from {{ source('raw_data', 'raw_telus_spend') }} as t
    group by t.account_description

    union all

    -- Rogers NGTA cellular
    select 'rogers'::text, 'raw_rogers_spend_cellular'::text, c.sub_bge
    from {{ source('raw_data', 'raw_rogers_spend_cellular') }} as c
    inner join {{ source('raw_data', 'ingestion_run') }} as r
        on r.ingestion_run_id = c.ingestion_run_id
    where r.provider = 'rogers'
    group by c.sub_bge

    union all

    -- Rogers NGTA data / voice
    select 'rogers'::text, 'raw_rogers_spend_data_voice'::text, v.sub_bge
    from {{ source('raw_data', 'raw_rogers_spend_data_voice') }} as v
    inner join {{ source('raw_data', 'ingestion_run') }} as r
        on r.ingestion_run_id = v.ingestion_run_id
    where r.provider = 'rogers'
    group by v.sub_bge
),

src as (
    select distinct
        vendor,
        source_table,
        case
            when vendor = 'telus' then {{ clean_text('raw_name') }}
            else nullif(trim(regexp_replace(raw_name, '[\x00-\x1f\x7f]', '', 'g')), '')
        end as sub_raw
    from raw_names
)

select distinct
    s.vendor,
    s.source_table,
    s.sub_raw as unmapped_sub_bge_name
from src s
left join {{ ref('sub_bge_alias_map') }} sbm
    on reference_data.match_key(sbm.raw_name) = reference_data.match_key(s.sub_raw)
where s.sub_raw is not null
    and sbm.raw_name is null
order by s.vendor, s.source_table, unmapped_sub_bge_name
