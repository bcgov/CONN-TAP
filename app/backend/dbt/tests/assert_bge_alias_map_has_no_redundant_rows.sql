{{ config(severity='warn') }}

-- Maintenance guard for bge_alias_map, which is matched by whole-token
-- containment (see reference_data.resolve_bge_alias), not exact equality.
--
-- Under containment a shorter alias already covers every longer spelling that
-- contains it: 'Fraser Health' matches 'FRASER HEALTH AUTHORITY' on its own, so
-- carrying both is dead weight -- the accumulation of near-duplicate rows this
-- matching was introduced to stop. This flags every row whose raw_name contains
-- another row's raw_name for the SAME bge_alias; each one can simply be deleted
-- from the seed with no change in behaviour.
--
-- Overlaps across DIFFERENT bge_alias targets are deliberately not reported
-- here: those are resolved by the longest-alias-wins rule in the macro (bare
-- 'GBC' -> Gov BC vs 'GBC - MINISTRY OF EDUCATION & CHILD CARE' -> ECC), which
-- is working as intended rather than a defect. See
-- scripts/validation/ngta/bge_alias_matching.sql for that report and for the
-- raw-name-level ambiguity check against real provider spellings.
--
-- Severity is 'warn': a redundant row is untidy, not broken.
--
-- One row per seed row to delete, not per (redundant, covering) pair -- a row
-- covered by two shorter aliases is still one deletion, and reporting the pairs
-- overstates the work.

select
    redundant.raw_name  as redundant_raw_name,
    redundant.bge_alias as bge_alias,
    string_agg(covering.raw_name, ' | ' order by covering.raw_name) as already_covered_by
from {{ ref('bge_alias_map') }} redundant
inner join {{ ref('bge_alias_map') }} covering
    on covering.raw_name <> redundant.raw_name
    and covering.bge_alias = redundant.bge_alias
    and reference_data.alias_matches(redundant.raw_name, covering.raw_name)
group by redundant.raw_name, redundant.bge_alias
order by redundant.bge_alias, redundant.raw_name
