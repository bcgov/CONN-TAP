{{ config(materialized='view') }}

select
    id,
    name,
    source,
    created_at
from {{ source('app', 'datasets') }}
