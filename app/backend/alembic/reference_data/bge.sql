CREATE TABLE IF NOT EXISTS reference_data.bge (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    sector_id   integer NOT NULL REFERENCES reference_data.sector(id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO reference_data.bge (code, name, sector_id) VALUES
    ('FHA',            'Fraser Health Authority',              (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('FNHA',           'First Nations Health Authority',       (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('IHA',            'Interior Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('NHA',            'Northern Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('PHSA',           'Provincial Health Services Authority', (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('VCHA (+PHC)',    'Vancouver Coastal Health Authority',   (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('VIHA',           'Vancouver Island Health Authority',    (SELECT id FROM reference_data.sector WHERE code = 'health_authorities')),
    ('BC Hydro',       'BC Hydro',                             (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('BCLC',           'BC Lottery Corporation',               (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('WSBC',           'WorkSafe BC',                          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    ('ICBC',           'Insurance Corporation of BC',          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations')),
    -- A made-up BGE: the districts aren't a real parent org, but they need somewhere
    -- to hang. Sits in the Gov & ECC sector alongside the ministries. Spend reported
    -- under ECC for a school district is routed here.
    ('School Districts','School Districts',                    (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc')),
    -- There is no ECC BGE: reports report Education & Child Care at BGE level, but in
    -- our system it is a ministry (sub-org) under Gov BC. Non-school-district ECC
    -- spend resolves to the 'Education and Child Care' sub_bge -- see sub_bge.sql.
    ('Gov BC',         'BC Government',             (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc'))
ON CONFLICT (code) DO NOTHING;
