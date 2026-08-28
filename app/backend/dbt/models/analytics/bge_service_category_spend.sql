{{ config(materialized='materialized_view') }}

-- Org-hierarchy x service-category aggregate. Finest grain the summary table needs:
-- period x provider x bge_id x sub_bge_id x service_category_id. sub_bge_id is
-- nullable (spend booked at the BGE with no sub-org). The API rolls the sub_bge
-- tree (sub_org / service_designee via entity_type + parent_sub_bge_id) and
-- resolves display names live from reference_data.
--
-- source_group collapses source_system into the two families the summary table
-- splits the BGE-direct "extra" by: TSMA (tsma + tsma_other) vs NGTA (rogers /
-- telus). It only meaningfully varies for BGE-direct (sub_bge_id null) rows; the
-- sub_bge tree rolls both together.
select
    dp.period_key,
    dp.calendar_year,
    dp.calendar_quarter,
    dp.fiscal_year,
    dp.fiscal_quarter,
    f.provider_id,
    f.bge_id,
    f.sub_bge_id,
    f.service_category_id,
    case when f.source_system in ('tsma', 'tsma_other') then 'tsma' else 'ngta' end as source_group,
    sum(f.spend_amount)::numeric(19, 4) as spend_amount,
    (sum(f.spend_amount) / 1000000.0)::numeric(19, 6) as spend_millions
from {{ ref('fct_service_spend') }} f
join {{ ref('dim_period') }} dp on dp.period_key = f.period_key
group by
    dp.period_key,
    dp.calendar_year,
    dp.calendar_quarter,
    dp.fiscal_year,
    dp.fiscal_quarter,
    f.provider_id,
    f.bge_id,
    f.sub_bge_id,
    f.service_category_id,
    case when f.source_system in ('tsma', 'tsma_other') then 'tsma' else 'ngta' end
