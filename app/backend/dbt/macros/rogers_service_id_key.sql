{# Cellular IDs drop a trailing 'M', as reporting.normalize_service_id does in the Rogers price validation. #}
{% macro rogers_service_id_key(column, cellular=false) -%}
    {%- if cellular -%}
        regexp_replace(upper({{ clean_text(column) }}), '(.)M$', '\1')
    {%- else -%}
        upper({{ clean_text(column) }})
    {%- endif -%}
{%- endmacro %}
