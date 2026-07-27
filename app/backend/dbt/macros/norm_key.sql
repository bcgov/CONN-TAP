{#
    Canonical match key for organization / sub-organization names.

    Alias-map and reference-code joins compare on this key so that matching is
    robust to the two ways raw provider text drifts from the seeded spellings:
      - case (Rogers emits "BC Min Finance", the seed had "BC MIN FINANCE")
      - invisible / mojibake junk (e.g. a trailing non-breaking space rendered
        as "Â ", which broke exact-byte matching on the Premier rows)

    It lowercases, strips every character outside printable ASCII (0x20-0x7e)
    -- which removes control chars, non-breaking spaces, and Latin-1 mojibake --
    then collapses whitespace runs and trims. Both sides of each join must wrap
    their column in this macro, and seed raw_name must be unique under it (see
    the assert_*_alias_raw_name_ci_unique tests) or a single spend line fans out.
#}
{% macro norm_key(col) -%}
    trim(regexp_replace(regexp_replace(lower({{ col }}), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g'))
{%- endmacro %}
