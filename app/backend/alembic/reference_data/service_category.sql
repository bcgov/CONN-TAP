CREATE TABLE IF NOT EXISTS reference_data.service_category (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO reference_data.service_category (code, name) VALUES
    ('cellular',                    'Cellular'),
    ('data',                        'Data'),
    ('voice',                       'Voice'),
    ('temporary_services',          'Temporary Services'),
    ('other_professional_services', 'Other Professional Services')
ON CONFLICT (code) DO NOTHING;
