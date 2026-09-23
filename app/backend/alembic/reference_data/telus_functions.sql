-- Telus detail-description normalization.
--
-- Kept out of functions.sql so a later migration can re-apply it on its own.
-- functions.sql must never be replayed on a live database: it ends with
-- DROP FUNCTION IF EXISTS raw_data.norm_key(text), and IF EXISTS does not
-- excuse a dependent object -- raw_data.v_rogers_cellular_validated, created
-- by the Rogers cellular validation run, is built on that function, so the
-- drop is rejected and the migration fails.
--
-- The same splitter rules as functions.sql apply here: alembic's
-- execute_sql_files splits on ';' with no dollar-quote awareness, so no
-- semicolon may appear inside a function body or any string literal.

-- Word signature of a Telus detail_description: anything in parentheses is
-- dropped, then every character that is not a letter, leaving single-spaced
-- words. Telus writes the financed amount, the term and the expiry date into
-- the label itself, so 'Easy Payment $27.50 - 2yrs (exp. Mar 2027)' and
-- 'Easy Payment $40.00 - 3 yrs (exp. Jan 2028)' both reduce to
-- 'easy payment yrs' and one seed entry covers every spelling of the charge.
--
-- Hardware matching only. The tax exclusions still compare literal text, where
-- the punctuation is part of the name ('pst-bc', 'gst/hst').
--
-- Returns '' for NULL, never NULL, so callers need no NULL handling.
CREATE OR REPLACE FUNCTION reference_data.telus_detail_signature(col text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT btrim(regexp_replace(
        regexp_replace(
            regexp_replace(lower(coalesce(col, '')), '\(.*?\)', ' ', 'g'),
            '\(.*$', ' '),
        '[^a-z]+', ' ', 'g'))
$$;

comment on function reference_data.telus_detail_signature(text) is
    'Word signature of a Telus detail_description -- parentheses and non-letters dropped';

-- TRUE when a detail_description is a Telus cellular hardware charge, whatever the
-- service id or statement category. Only half the rule -- callers still require the
-- row to be wireless-sourced or source_id 164 before trusting it as cellular
-- hardware. See scripts/sql/telus_classification.md for the confirmations.
--
-- The list itself lives in the dbt seed and nowhere else, so adding a confirmed
-- hardware family is a one-line edit to seeds/telus_hardware_details.csv that every
-- caller picks up -- the dbt models, the validation checks and the pricebook scripts
-- alike.
--
-- check_function_bodies is disabled for this statement because the body reads
-- seeds.telus_hardware_details, a dbt-managed table that does not exist yet when this
-- migration runs. The reference resolves at call time, by which point `dbt seed` has
-- built it. Same arrangement as reference_data.resolve_bge_alias.
SET check_function_bodies = off;

CREATE OR REPLACE FUNCTION reference_data.telus_is_hardware_detail(p_detail text)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM seeds.telus_hardware_details h
        WHERE h.detail_description = reference_data.telus_detail_signature(p_detail)
    )
$$;

RESET check_function_bodies;

comment on function reference_data.telus_is_hardware_detail(text) is
    'TRUE when a Telus detail_description matches a hardware signature in seeds.telus_hardware_details';
