CREATE TABLE IF NOT EXISTS reference_data.provider (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO reference_data.provider (code, name) VALUES
    ('telus',  'TELUS'),
    ('rogers', 'Rogers')
ON CONFLICT (code) DO NOTHING;
