{# TELUS bills have no service ID column. Codes written in the description are possible ones
   (NGLL22, XPULNA5GB): words of 4+ letters and digits with at least one of each.
   Returns every such word; a description can have several, and the list is empty when it has none.
   Which one is in the pricebook is decided in int_telus_ngta_spend. #}
{% macro extract_telus_service_ids(column) -%}
    array(
        select word
        from regexp_split_to_table(upper({{ column }}), '[^A-Z0-9]+') as word
        where length(word) >= 4
            and word ~ '[A-Z]'
            and word ~ '[0-9]'
    )
{%- endmacro %}
