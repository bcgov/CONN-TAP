{{ config(materialized='view') }}

{% set pricebooks = [
    ('raw_rogers_v2_cellular_pricebook',              'cellular'),
    ('raw_rogers_v2_cellular_device_pricebook',       'cellular_hardware'),
    ('raw_rogers_v2_data_pricebook',                  'data'),
    ('raw_rogers_v2_voice_pricebook',                 'voice'),
    ('raw_rogers_v2_professional_services_pricebook', 'professional_services'),
] %}

{% for pricebook, service_category in pricebooks %}
select distinct
    {{ rogers_service_id_key('service_id', cellular=(service_category == 'cellular')) }} as service_id_key,
    '{{ service_category }}'::text as service_category_code
from {{ source('raw_data', pricebook) }}
where {{ clean_text('service_id') }} is not null
{% if not loop.last %}union all{% endif %}
{% endfor %}
