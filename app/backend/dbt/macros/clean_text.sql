{#
    Normalise a raw text value before it is matched against seed lists or aliases:
    control characters (tabs, line breaks, ...) become spaces, runs of spaces
    collapse to one, the ends are trimmed, and an empty result becomes null.

    Control characters are replaced rather than deleted so words separated only by
    a line break stay separate ('Easy<LF>Payment' -> 'Easy Payment', not
    'EasyPayment'). The seed lists compared against (telus_excluded_*,
    telus_hardware_details) hold single-spaced, trimmed values, so this can only add
    matches, never break one.

    strip_star=true also drops TELUS's trailing '*' ('HIGH SPEED ACCESS *' -> 'HIGH SPEED ACCESS'),
    for matching bill descriptions to pricebook IDs and the TLS list.
#}
{% macro clean_text(column, strip_star=false) -%}
    {%- if strip_star -%}
    nullif(trim(rtrim(trim(regexp_replace({{ column }}, '[\x00-\x20\x7f]+', ' ', 'g')), '*')), '')
    {%- else -%}
    nullif(trim(regexp_replace({{ column }}, '[\x00-\x20\x7f]+', ' ', 'g')), '')
    {%- endif -%}
{%- endmacro %}
