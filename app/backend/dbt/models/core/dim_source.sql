{{ config(materialized='table') }}

select
    source,
    count(*) as dataset_count,
    min(created_at) as first_loaded_at,
    max(created_at) as last_loaded_at
from {{ ref('stg_datasets') }}
group by source
