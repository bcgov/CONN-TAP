-- Shared helper functions for reference-data lookups.
--
-- NOTE: alembic's execute_sql_files splits these files on ';' without any
-- dollar-quote awareness (see migration_utils._split_sql_statements), so a
-- function body must not contain a semicolon or the CREATE gets cut in half
-- and the migration fails. The trailing ';' inside a $$ body is optional --
-- leave it off. A body that genuinely needs multiple statements would need
-- that splitter taught about $$ first.
--
-- Lives in the database (rather than as a dbt macro) so the dbt models and the
-- standalone psql scripts under scripts/validation/ can call the same code --
-- the latter cannot expand Jinja, which is why this predicate used to be
-- duplicated as telus_bge_alias_matches in telus_validation.sql.

-- Canonical match key for organization / sub-organization names. Exact
-- alias-map and reference-code joins compare on this key so matching survives
-- the two ways raw provider text drifts from the seeded spellings:
--   - case (Rogers emits "BC Min Finance", the seed had "BC MIN FINANCE")
--   - invisible / mojibake junk (a trailing non-breaking space rendered as
--     "Â ", which broke exact-byte matching on the Premier rows)
--
-- It lowercases, strips every character outside printable ASCII (0x20-0x7e) --
-- removing control chars, non-breaking spaces and Latin-1 mojibake -- then
-- collapses whitespace runs and trims. Both sides of such a join must wrap
-- their column in this.
--
-- Caveat: an alias map's raw_name must be unique under this key, or one spend
-- line matches two alias rows and fans out into double-counted spend. Nothing
-- currently enforces that; it holds by inspection today.
CREATE OR REPLACE FUNCTION reference_data.norm_key(col text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT trim(regexp_replace(regexp_replace(lower(col), '[^\x20-\x7e]', '', 'g'), '\s+', ' ', 'g'))
$$;

comment on function reference_data.norm_key(text) is
    'Canonical match key for organization names: lowercased, non-printable-ASCII stripped, whitespace collapsed';

-- Superseded by the two functions here; dropped in case an older run of
-- scripts/validation/rogers/_shared.sql left it behind.
DROP FUNCTION IF EXISTS raw_data.norm_key(text);

CREATE OR REPLACE FUNCTION reference_data.alias_matches(p_raw text, p_alias text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
    -- Whole-token containment, not a bare substring test: both sides collapse
    -- their non-alphanumeric runs to single spaces and are padded with a
    -- leading/trailing space, so 'SD' matches 'SD 37 Delta' but not 'BCSD'.
    SELECT p_raw IS NOT NULL AND p_alias IS NOT NULL AND strpos(
        ' ' || lower(regexp_replace(p_raw,   '[^[:alnum:]]+', ' ', 'g')) || ' ',
        ' ' || lower(regexp_replace(p_alias, '[^[:alnum:]]+', ' ', 'g')) || ' '
    ) > 0
$$;

comment on function reference_data.alias_matches(text, text) is
    'True when the raw name contains the alias as a whole token or phrase, case-insensitively';

-- Resolve a raw organization name to its canonical BGE code -- the one place the
-- matching rule lives, called by the dbt staging models and by the Rogers and
-- Telus validation reports alike.
--
-- Containment can match several alias rows at once, so the pick has to be
-- narrowed to exactly one or a spend line would fan out into double-counted
-- spend. ORDER BY length DESC is the rule: the most specific fragment wins, so
-- 'GBC - MINISTRY OF EDUCATION & CHILD CARE' (-> ECC) beats bare 'GBC'
-- (-> Gov BC) on a name carrying both. raw_name breaks any remaining tie so the
-- answer is deterministic rather than scan-order dependent.
--
-- check_function_bodies is disabled for this one statement because the body
-- reads seeds.bge_alias_map, a dbt-managed table that does not exist yet when
-- this migration runs. The reference resolves at call time, by which point
-- `dbt seed` has built it. The cost is that a typo in the body surfaces on
-- first call rather than at migration time.
SET check_function_bodies = off;

CREATE OR REPLACE FUNCTION reference_data.resolve_bge_alias(p_raw text)
RETURNS text
LANGUAGE sql
STABLE
AS $$
    SELECT bm.bge_alias
    FROM seeds.bge_alias_map bm
    WHERE reference_data.alias_matches(p_raw, bm.raw_name)
    ORDER BY length(bm.raw_name) DESC, bm.raw_name
    LIMIT 1
$$;

RESET check_function_bodies;

comment on function reference_data.resolve_bge_alias(text) is
    'Canonical BGE code for a raw organization name: longest whole-token alias match from seeds.bge_alias_map';
