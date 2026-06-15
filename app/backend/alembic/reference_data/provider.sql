INSERT INTO reference_data.provider (code, name) VALUES
    ('telus',  'TELUS'),
    ('rogers', 'Rogers')
ON CONFLICT (code) DO NOTHING;
