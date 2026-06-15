INSERT INTO reference_data.service_category (code, name) VALUES
    ('cellular',                    'Cellular'),
    ('data',                        'Data'),
    ('voice',                       'Voice'),
    ('temporary_services',          'Temporary Services'),
    ('other_professional_services', 'Other Professional Services')
ON CONFLICT (code) DO NOTHING;
