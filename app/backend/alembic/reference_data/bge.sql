INSERT INTO reference_data.bge (code, name, sector_id) VALUES
    ('FHA',            'Fraser Health Authority',              (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('FNHA',           'First Nations Health Authority',       (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('IHA',            'Interior Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('NHA',            'Northern Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('PHSA',           'Provincial Health Services Authority', (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('VCHA (+PHC)',    'Vancouver Coastal Health + Providence',(SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('VIHA',           'Vancouver Island Health Authority',    (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('BC Hydro',       'BC Hydro',                             (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('BCLC',           'BC Lottery Corporation',               (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('WSBC',           'WorkSafe BC',                          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('ICBC',           'Insurance Corporation of BC',          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('School Districts','School Districts',                    (SELECT id FROM reference_data.sector WHERE code = 'school_districts')),
    ('ECC',            'Education and Child Care',             (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc')),
    ('Gov BC',         'BC Government Ministries',             (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc'))
ON CONFLICT (code) DO NOTHING;
