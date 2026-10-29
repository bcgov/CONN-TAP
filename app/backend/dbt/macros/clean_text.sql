{#
    Normalise a raw text value before it is matched against seed lists or aliases:
    control characters (tabs, line breaks, ...) become spaces, runs of spaces
    collapse to one, the ends are trimmed, and an empty result becomes null.

    Control characters are replaced rather than deleted so words separated only by
    a line break stay separate ('Easy<LF>Payment' -> 'Easy Payment', not
    'EasyPayment'). The seed lists compared against (telus_excluded_*,
    telus_hardware_details) hold single-spaced, trimmed values, so this can only add
    matches, never break one.

    strip_punctuation=true also turns anything that isn't a letter or digit into a space, for
    matching bill descriptions to the pricebooks and the TLS list. TELUS's trailing '*' goes too:
    'HIGH SPEED ACCESS *' -> 'HIGH SPEED ACCESS', 'Off Premise Extension, Add''l' -> 'Off Premise Extension Add l'.
#}
{% macro clean_text(column, strip_punctuation=false) -%}
    {%- if strip_punctuation -%}
    nullif(trim(regexp_replace({{ column }}, '[^A-Za-z0-9]+', ' ', 'g')), '')
    {%- else -%}
    nullif(trim(regexp_replace({{ column }}, '[\x00-\x20\x7f]+', ' ', 'g')), '')
    {%- endif -%}
{%- endmacro %}
