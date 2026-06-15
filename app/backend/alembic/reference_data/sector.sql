INSERT INTO reference_data.sector (code, name) VALUES
    ('health_authorities', 'Health Authorities'),
    ('crown_corporations', 'Crown Corporations'),
    ('school_districts',   'School Districts'),
    ('gov_ecc',            'Gov & ECC')
ON CONFLICT (code) DO NOTHING;
