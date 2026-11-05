{# TELUS bills have no service ID column. Codes written in the description are possible ones
   (NGLL22, XPULNA5GB, TEL-7010): words of 4+ characters with at least one letter and one digit.
   Hyphens become spaces, the same way the pricebook IDs are cleaned (TEL-7010 -> 'TEL 7010').
   Returns every such word; which one is in the pricebook is decided in int_telus_ngta_spend. #}
{% macro extract_telus_service_ids(column) -%}
    array(
        select replace(word, '-', ' ')
        from regexp_split_to_table(upper({{ column }}), '[^A-Z0-9-]+') as word
        where length(word) >= 4
            and word ~ '[A-Z]'
            and word ~ '[0-9]'
    )
{%- endmacro %}
