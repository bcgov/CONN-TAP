CREATE TABLE IF NOT EXISTS reference_data.sector (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO reference_data.sector (code, name) VALUES
    ('health_authorities', 'Health Authorities'),
    ('crown_corporations', 'Crown Corporations'),
    ('school_districts',   'School Districts'),
    ('gov_ecc',            'Gov & ECC')
ON CONFLICT (code) DO NOTHING;
