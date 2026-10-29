{{ config(materialized='view') }}

-- All TELUS pricebooks in one format: one row per pricebook row, with its service ID,
-- rate plan / service / description (where the pricebook has them) and service category.
-- priority: when a value is in more than one pricebook, the lowest number wins (TLS first).

with pricebooks as (
    select service_id, null::text as rate_plan, null::text as service, null::text as description, product,
           'time_limited_services' as service_category_code, 1 as priority
    from {{ source('raw_data', 'raw_telus_v2_tls_pricebook') }}
    union all
    select service_id, null, null, null, null, 'professional_services', 2
    from {{ source('raw_data', 'raw_telus_v2_professional_services_pricebook') }}
    union all
    select service_id, null, null, description, null, 'professional_services', 3
    from {{ source('raw_data', 'raw_telus_v2_connected_worker_professional_services_pricebook') }}
    union all
    select service_id, null, null, description, null, 'cellular_hardware', 4
    from {{ source('raw_data', 'raw_telus_v2_connected_worker_hardware_pricebook') }}
    union all
    select service_id, null, null, description, null, 'cellular', 5
    from {{ source('raw_data', 'raw_telus_v2_connected_worker_pricebook') }}
    union all
    select service_id, null, null, description, null, 'cellular', 6
    from {{ source('raw_data', 'raw_telus_v2_connected_worker_usage_rate_pricebook') }}
    union all
    select service_id, null, service, null, null, 'cellular', 7
    from {{ source('raw_data', 'raw_telus_v2_gms_pricebook') }}
    union all
    -- Fleet Complete has no service_id column; its code is the service ID
    select code, null, null, description, null, 'cellular', 8
    from {{ source('raw_data', 'raw_telus_v2_fleet_complete_pricebook') }}
    union all
    select service_id, null, null, item_description, null, 'cellular', 9
    from {{ source('raw_data', 'raw_telus_v2_control_center_pricebook') }}
    union all
    select service_id, null, service, null, null, 'cellular', 10
    from {{ source('raw_data', 'raw_telus_v2_cellular_mms_pricebook') }}
    union all
    select service_id, null, service, null, null, 'cellular', 11
    from {{ source('raw_data', 'raw_telus_v2_cellular_additional_fee_based_features_pricebook') }}
    union all
    select service_id, null, service, description, null, 'voice', 12
    from {{ source('raw_data', 'raw_telus_v2_voice_data_usage_rates_pricebook') }}
    union all
    select service_id, null, null, null, null, 'data', 13
    from {{ source('raw_data', 'raw_telus_v2_data_services_pricebook') }}
    union all
    select service_id, null, null, null, null, 'voice', 14
    from {{ source('raw_data', 'raw_telus_v2_voice_services_pricebook') }}
    union all
    select service_id, rate_plan, null, null, null, 'cellular', 15
    from {{ source('raw_data', 'raw_telus_v2_cellular_services_pricebook') }}
)

select distinct
    -- punctuation and the trailing '*' are ignored (TLS IDs are descriptions like 'CARRIER ETHERNET OPTICAL 1GB*')
    upper({{ clean_text('service_id', strip_punctuation=true) }}) as service_id,
    upper({{ clean_text('rate_plan', strip_punctuation=true) }}) as rate_plan,
    upper({{ clean_text('service', strip_punctuation=true) }}) as service,
    upper({{ clean_text('description', strip_punctuation=true) }}) as description,
    service_category_code,
    -- Sub-category from the TLS pricebook tab the row is on
    case product
        when 'SIPA V1' then 'tls_sipa'
        when 'Copper Services' then 'tls_copper'
        when 'IP Trunking R2' then 'tls_ip_trunking_r2'
        when 'Carrier Optical Ethernet' then 'tls_optical_ethernet'
        when 'Centrex' then 'tls_centrex'
        when 'Analog Private Line' then 'tls_analog_private_line'
        when 'Managed Router' then 'tls_managed_router'
        -- 'ADSL Services' covers both the voice and the data bill, so the LTO list decides those
    end as sub_category_code,
    priority
from pricebooks
where {{ clean_text('service_id', strip_punctuation=true) }} is not null
