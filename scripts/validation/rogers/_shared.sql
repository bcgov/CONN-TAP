-- Shared helpers for the Rogers validation reports. Each runner applies this file first,
-- before its per-report validation SQL and the spend comparison, so these objects exist once
-- and every report resolves names the same way.

-- Canonical match key for organization / sub-organization names. Replicates the dbt
-- `norm_key` macro that the staging models (stg_rogers_spend) use to join raw provider
-- names to the alias maps, so the validations match names exactly the way the pipeline does:
-- lowercase, strip non-printable/mojibake chars, collapse whitespace, trim. Both sides of
-- every alias-map join wrap their column in this.
CREATE OR REPLACE FUNCTION raw_data.norm_key(col text)
RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT trim(regexp_replace(regexp_replace(lower(col), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g'))
$$;
