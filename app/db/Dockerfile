# syntax=docker/dockerfile:1.7
# Postgres 16 with pg_partman, pg_trgm, btree_gin/gist available.
FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-partman \
    && rm -rf /var/lib/apt/lists/*
