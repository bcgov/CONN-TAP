-- Example partitioned fact table managed by pg_partman.
-- Range-partitioned by day on event_time. The FastAPI app's `datasets`
-- table is created by SQLAlchemy on startup; this file shows the pattern
-- for partitioning high-volume tables.

CREATE TABLE IF NOT EXISTS public.events (
    event_id    BIGSERIAL,
    event_time  TIMESTAMPTZ NOT NULL,
    source      TEXT        NOT NULL,
    payload     JSONB       NOT NULL,
    PRIMARY KEY (event_id, event_time)
) PARTITION BY RANGE (event_time);

-- Helpful indexes on the parent (propagated to partitions).
CREATE INDEX IF NOT EXISTS events_source_idx     ON public.events (source);
CREATE INDEX IF NOT EXISTS events_payload_gin    ON public.events USING GIN (payload);
CREATE INDEX IF NOT EXISTS events_source_trgm    ON public.events USING GIN (source gin_trgm_ops);

-- Register with pg_partman for automatic daily partitions, retaining 90 days.
-- pg_partman v5 removed the legacy 'native' p_type; the supported types are
-- 'range' and 'list'. Use 'range' for time-based partitioning.
SELECT partman.create_parent(
    p_parent_table   => 'public.events',
    p_control        => 'event_time',
    p_type           => 'range',
    p_interval       => '1 day',
    p_premake        => 7
)
WHERE NOT EXISTS (
    SELECT 1 FROM partman.part_config WHERE parent_table = 'public.events'
);

UPDATE partman.part_config
   SET retention = '90 days',
       retention_keep_table = false
 WHERE parent_table = 'public.events';
