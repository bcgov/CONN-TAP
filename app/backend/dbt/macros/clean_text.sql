{#
    Normalise a raw text value before it is matched against seed lists or aliases:
    control characters (tabs, line breaks, ...) become spaces, runs of spaces
    collapse to one, the ends are trimmed, and an empty result becomes null.

    Control characters are replaced rather than deleted so words separated only by
    a line break stay separate ('Easy<LF>Payment' -> 'Easy Payment', not
    'EasyPayment'). The seed lists compared against (telus_excluded_*,
    telus_hardware_details) hold single-spaced, trimmed values, so this can only add
    matches, never break one.
#}
{% macro clean_text(column) -%}
    nullif(trim(regexp_replace({{ column }}, '[\x00-\x20\x7f]+', ' ', 'g')), '')
{%- endmacro %}
