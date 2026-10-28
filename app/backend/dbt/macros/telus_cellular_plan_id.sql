{# GoBC / TSMA cellular plan name -> cellular pricebook service_id, as in scripts/build_telus_unmatched.py (_CELL_MAP). #}
{% macro telus_cellular_plan_id(column) -%}
    case
        when {{ column }} ~* 'GoBC V&D ULNA [0-9]+GB' then
            'XPULNA'
            || regexp_replace({{ column }}, '.*V&D ULNA ([0-9]+)GB.*', '\1', 'i')
            || case
                when regexp_replace({{ column }}, '.*V&D ULNA ([0-9]+)GB.*', '\1', 'i')
                    in ('1', '2', '3', '4', '5', '6', '7', '8', '9') then 'GB'
                else 'G'
            end
        when {{ column }} ilike 'GoBC Data 5GB%' then 'XPTMHS5GB'
        when {{ column }} ilike 'GoBC Data 10GB%' then 'XPTMHS10G'
        when {{ column }} ilike 'GoBC Voice ULNA%' then 'XPULNAV01'
        when {{ column }} ilike '%High Capacity Data 500GB%' then 'XPDAT500G'
        when {{ column }} ilike '%High Capacity Data 100GB%' then 'XPDAT100G'
        when {{ column }} ilike '%High Capacity Data Access%'
            or {{ column }} ilike 'TSMA Data Access%' then 'XPHCDATAC'
        when {{ column }} ilike '%Public Static IP%' then 'XSNGTASIP'
        when {{ column }} ilike '%Visual Voicemail%' then 'XSNGTAVVM'
        when {{ column }} ilike '%Network Priority%' then 'XSNGTAPRI'
        when {{ column }} ilike '%Vacation Disconnect%' then 'XPVAD5'
    end
{%- endmacro %}
