-- Bootstrap extensions for partitioning and advanced indexing.
-- pg_partman handles automated partition management.
-- pg_trgm enables trigram GIN indexes for fast text search.
-- btree_gin / btree_gist allow mixed-type GIN/GIST indexes.

CREATE SCHEMA IF NOT EXISTS partman;

CREATE EXTENSION IF NOT EXISTS pg_partman SCHEMA partman;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE SCHEMA IF NOT EXISTS analytics;
