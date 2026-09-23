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
