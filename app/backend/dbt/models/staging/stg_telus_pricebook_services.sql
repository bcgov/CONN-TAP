{{ config(materialized='view') }}

-- Listed in priority order: an ID found in more than one pricebook takes the first one.
-- TLS comes first.
{% set pricebooks = [
    ('raw_telus_v2_tls_pricebook',                                       'service_id', 'time_limited_services'),
    ('raw_telus_v2_professional_services_pricebook',                     'service_id', 'professional_services'),
    ('raw_telus_v2_connected_worker_professional_services_pricebook',    'service_id', 'professional_services'),
    ('raw_telus_v2_connected_worker_hardware_pricebook',                 'service_id', 'cellular_hardware'),
    ('raw_telus_v2_connected_worker_pricebook',                          'service_id', 'cellular'),
    ('raw_telus_v2_connected_worker_usage_rate_pricebook',               'service_id', 'cellular'),
    ('raw_telus_v2_gms_pricebook',                                       'service_id', 'cellular'),
    ('raw_telus_v2_fleet_complete_pricebook',                            'code',       'cellular'),
    ('raw_telus_v2_control_center_pricebook',                            'service_id', 'cellular'),
    ('raw_telus_v2_cellular_mms_pricebook',                              'service_id', 'cellular'),
    ('raw_telus_v2_cellular_additional_fee_based_features_pricebook',    'service_id', 'cellular'),
    ('raw_telus_v2_voice_data_usage_rates_pricebook',                    'service_id', 'voice'),
    ('raw_telus_v2_data_services_pricebook',                             'service_id', 'data'),
    ('raw_telus_v2_voice_services_pricebook',                            'service_id', 'voice'),
    ('raw_telus_v2_cellular_services_pricebook',                         'service_id', 'cellular'),
] %}

with pricebook_services as (
{% for pricebook, id_column, service_category in pricebooks %}
    select distinct
        -- the trailing '*' is ignored (TLS IDs are descriptions like 'CARRIER ETHERNET OPTICAL 1GB*')
        upper({{ clean_text(id_column, strip_star=true) }}) as service_id_key,
        '{{ service_category }}'::text as service_category_code,
        {{ loop.index }} as priority
    from {{ source('raw_data', pricebook) }}
    where {{ clean_text(id_column, strip_star=true) }} is not null
    {% if not loop.last %}union all{% endif %}
{% endfor %}
),

-- TLS sub-category from the pricebook tab the ID is listed on.
tls_sub_categories as (
    select distinct
        upper({{ clean_text('service_id', strip_star=true) }}) as service_id_key,
        case product
            when 'SIPA V1' then 'tls_sipa'
            when 'Copper Services' then 'tls_copper'
            when 'IP Trunking R2' then 'tls_ip_trunking_r2'
            when 'Carrier Optical Ethernet' then 'tls_optical_ethernet'
            when 'Centrex' then 'tls_centrex'
            when 'Analog Private Line' then 'tls_analog_private_line'
            when 'Managed Router' then 'tls_managed_router'
            -- 'ADSL Services' covers both the voice and the data bill, so the LTO list decides those
        end as sub_category_code
    from {{ source('raw_data', 'raw_telus_v2_tls_pricebook') }}
    where {{ clean_text('service_id', strip_star=true) }} is not null
)

select distinct on (pb.service_id_key)
    pb.service_id_key,
    pb.service_category_code,
    case when pb.service_category_code = 'time_limited_services' then tls.sub_category_code end as sub_category_code
from pricebook_services pb
left join tls_sub_categories tls on tls.service_id_key = pb.service_id_key
order by pb.service_id_key, pb.priority
