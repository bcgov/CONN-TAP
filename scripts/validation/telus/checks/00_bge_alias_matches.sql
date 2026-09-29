-- Shared BGE alias matcher for the Telus validators
-- (see app/backend/alembic/raw_data/ngta_postgres.sql).
--
-- Case-insensitive "does this sheet name contain the alias as a whole token/phrase" test.
-- Used by 09_all_bges_in_sheets, 10_new_bges_in_sheets and 12_still_missing_bges_in_sheets;
-- load this file before those, since Postgres validates SQL function bodies at CREATE time.

DROP FUNCTION IF EXISTS telus_bge_alias_matches (text, text);
CREATE OR REPLACE FUNCTION telus_bge_alias_matches (p_sheet text, p_alias text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT strpos(
    ' ' || lower(regexp_replace(p_sheet, '[^[:alnum:]]+', ' ', 'g')) || ' ',
    ' ' || lower(regexp_replace(p_alias, '[^[:alnum:]]+', ' ', 'g')) || ' '
  ) > 0;
$$;
