-- Shared helper functions for reference-data lookups.
--
-- NOTE: alembic's execute_sql_files splits these files on ';' without any
-- dollar-quote awareness (see migration_utils._split_sql_statements), so a
-- function body must not contain a semicolon or the CREATE gets cut in half
-- and the migration fails. The trailing ';' inside a $$ body is optional --
-- leave it off. A body that genuinely needs multiple statements would need
-- that splitter taught about $$ first. The same applies to comment text:
-- no semicolon may appear inside ANY string literal, or the statement is
-- cut in half ('Join on this; never match partially' did exactly that).
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

-- ---------------------------------------------------------------------------
-- Alias matching
--
-- Every alias lookup in the project is a plain equi-join on match_key:
--     join alias_map on match_key(alias_map.raw_name) = match_key(raw_column)
-- Both sides are cleaned the same way, so a lookup either hits exactly one row
-- or none. Nothing ranks candidates and nothing matches partially, which is
-- what keeps it a hash join and keeps spend from drifting between entities.
-- ---------------------------------------------------------------------------

-- Words that carry no identity. Kept as a list so it can be read and edited one
-- word at a time; match_key builds its pattern from this and nothing else
-- hardcodes them.
--
-- Every word is a bet that it never distinguishes two entities. Province words
-- (british, columbia) are deliberately absent: with them,
-- 'BRITISH COLUMBIA EMERGENCY' (PHSA) and 'GBC-MINISTRY OF EMERGENCY'
-- (Emergency Management) both reduce to 'emergency'.
-- assert_alias_map_keys_unique fails if any two rows ever collide that way.
CREATE OR REPLACE FUNCTION reference_data.alias_filler_pattern()
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT '\m(' || array_to_string(ARRAY[
        -- grammar
        'a', 'an', 'and', 'as', 'at', 'by', 'for', 'in', 'of', 'on', 'the', 'to',
        -- corporate suffixes
        'corp', 'corporation', 'inc', 'ltd',
        -- org-structure words
        'auth', 'authority', 'dept', 'department', 'min', 'ministry',
        'office', 'offices',
        -- address / billing noise
        'attn', 'c o', 'ngta', 'no', 'po',
        -- province qualifiers (british / columbia are NOT safe -- see above)
        'bc', 'gbc'
    ], '|') || ')\M'
$$;

comment on function reference_data.alias_filler_pattern() is
    'Words match_key discards. Edit the array, not the pattern.';

-- THE matching key. Three outcomes, first one wins:
--   1. a school district      -> 'schooldistrict39'
--   2. anything else          -> its meaningful words, squashed ('health')
--   3. nothing but filler     -> kept literally ('GBC' -> 'gbc'), because an
--                               empty key would make every such name collide
CREATE OR REPLACE FUNCTION reference_data.match_key(col text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT coalesce(
        'schooldistrict' || s.district_number,
        nullif(replace(s.clean_words, ' ', ''), ''),
        replace(s.words, ' ', '')
    )
    FROM (
        SELECT
            -- Matched on clean_words, so the pattern needs no 'NO.' / '#'
            -- handling: punctuation is already gone and 'no' is filler. Two
            -- plain patterns rather than one alternation, because a
            -- non-capturing group contains a colon and SQLAlchemy's text()
            -- would read that as a bind parameter when alembic runs this file.
            coalesce(
                substring(c.clean_words from '\mschool dist[a-z]* 0*([0-9]{1,3})\M'),
                substring(c.clean_words from '\msd 0*([0-9]{1,3})\M'),
                -- 'NO85' with no space survives as one token, so 'no' is never
                -- stripped as filler: 'SCHOOL DISTRICT NO85 VANCOUVER ISLAND NORTH'
                substring(c.words      from '\mschool dist[a-z]* no0*([0-9]{1,3})\M')
            ) AS district_number,
            c.clean_words,
            c.words
        FROM (
            SELECT
                w.words,
                -- words minus filler, whitespace re-collapsed
                btrim(regexp_replace(
                    regexp_replace(w.words, reference_data.alias_filler_pattern(), ' ', 'g'),
                    '\s+', ' ', 'g')) AS clean_words
            FROM (
                -- lowercase, drop mojibake and control chars, punctuation -> spaces
                SELECT btrim(regexp_replace(
                           lower(regexp_replace(col, '[^\x20-\x7e]', '', 'g')),
                           '[^a-z0-9]+', ' ', 'g')) AS words
            ) w
        ) c
    ) s
$$;

comment on function reference_data.match_key(text) is
    'Canonical alias-matching key. Join on this -- never match partially.';

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
        ' ' || lower(regexp_replace(p_raw,   '[^a-zA-Z0-9]+', ' ', 'g')) || ' ',
        ' ' || lower(regexp_replace(p_alias, '[^a-zA-Z0-9]+', ' ', 'g')) || ' '
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
