{{ config(severity='warn') }}

-- Alias -> reference-data gap check: flags sub_bge_alias values in
-- sub_bge_alias_map that do not resolve to a code in reference_data.sub_bge.
--
-- Severity is 'warn' by design: sub_bge aliases for a not-yet-loaded or retired
-- entity are intentionally allowed (see the note in seeds/_seeds.yml), so this
-- surfaces gaps for review without failing the build. Flip to 'error' above if
-- you want unresolved sub_bge aliases to break `dbt build`.
--
-- BGE codes are skipped: some raw sub-org spellings are labelled at BGE level and
-- carried in the alias map as a BGE code (e.g. the 'ECC' remap). Those are not
-- expected to exist in reference_data.sub_bge, so they are excluded here rather
-- than reported as false gaps.
--
-- The reference join mirrors the exact-equality code match used downstream in
-- int_service_spend_line_items (sb.code = coalesce(sm.sub_bge_alias, ...)).

select
    m.sub_bge_alias,
    count(*)                                   as alias_row_count,
    string_agg(m.raw_name, ' | ' order by m.raw_name) as raw_names
from {{ ref('sub_bge_alias_map') }} m
left join {{ source('reference_data', 'sub_bge') }} sb
    on sb.code = m.sub_bge_alias
-- skip aliases that are BGE-level codes, not sub_bge codes
left join {{ source('reference_data', 'bge') }} b
    on b.code = m.sub_bge_alias
where m.sub_bge_alias is not null
    and sb.id is null
    and b.id is null
group by m.sub_bge_alias
order by m.sub_bge_alias
