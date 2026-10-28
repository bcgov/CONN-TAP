{#
    Matching key for free-text descriptions compared against a seed list:
    lowercase, every run of characters that isn't a letter, digit or '%' becomes
    one space, ends trimmed. Spacing and punctuation then don't matter, so
    'Office Phone- Device Down Payment' and 'office phone - device down payment'
    are the same key. '%' is kept so seed entries still work as LIKE patterns.
    Apply it to BOTH sides of a comparison.
#}
{% macro text_key(column) -%}
    trim(regexp_replace(lower({{ column }}), '[^a-z0-9%]+', ' ', 'g'))
{%- endmacro %}
