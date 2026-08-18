CREATE TABLE IF NOT EXISTS reference_data.bge (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    sector_id   integer NOT NULL REFERENCES reference_data.sector(id),
    onboarded   boolean NOT NULL DEFAULT false,
    cellular    text,
    data        text,
    voice       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

comment on table reference_data.bge is 'List of Buyer Group Entities (BGEs) TO office defines';
comment on column reference_data.bge.id is 'Unique ID for the BGE';
comment on column reference_data.bge.code is 'Unique code for the BGE, used to resolve aliases';
comment on column reference_data.bge.name is 'Display name';
comment on column reference_data.bge.description is 'Description of the BGE';
comment on column reference_data.bge.sector_id is 'Sector the BGE belongs to';
comment on column reference_data.bge.onboarded is 'Whether the entity has been onboarded to NGTA/TSMA';
comment on column reference_data.bge.cellular is 'Who provides cellular service: Self, CSBC, ECC, PHSA or n/a';
comment on column reference_data.bge.data is 'Who provides data service: Self, CSBC, ECC, PHSA or n/a';
comment on column reference_data.bge.voice is 'Who provides voice service: Self, CSBC, ECC, PHSA or n/a';

INSERT INTO reference_data.bge (code, name, sector_id, onboarded, cellular, data, voice) VALUES
    ('FHA',            'Fraser Health Authority',              (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('FNHA',           'First Nations Health Authority',       (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('IHA',            'Interior Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('NHA',            'Northern Health Authority',            (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('PHSA',           'Provincial Health Services Authority', (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('VCHA (+PHC)',    'Vancouver Coastal Health Authority',   (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'PHSA', 'PHSA', 'PHSA'),
    ('VIHA',           'Vancouver Island Health Authority',    (SELECT id FROM reference_data.sector WHERE code = 'health_authorities'), true, 'Self', 'Self', 'Self'),
    ('BC Hydro',       'BC Hydro',                             (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations'), true, 'Self', 'Self', 'Self'),
    ('BCLC',           'BC Lottery Corporation',               (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations'), true, 'Self', 'Self', 'Self'),
    ('WSBC',           'WorkSafe BC',                          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations'), true, 'Self', 'Self', 'Self'),
    ('ICBC',           'Insurance Corporation of BC',          (SELECT id FROM reference_data.sector WHERE code = 'crown_corporations'), true, 'Self', 'Self', 'Self'),
    -- A made-up BGE: the districts aren't a real parent org, but they need somewhere
    -- to hang. Sits in the Gov & ECC sector alongside the ministries. Spend reported
    -- under ECC for a school district is routed here.
    ('School Districts','School Districts',                    (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc'), true, NULL, NULL, NULL),
    -- There is no ECC BGE: reports report Education & Child Care at BGE level, but in
    -- our system it is a ministry (sub-org) under Gov BC. Non-school-district ECC
    -- spend resolves to the 'Education and Child Care' sub_bge -- see sub_bge.sql.
    ('Gov BC',         'BC Government',             (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc'), true, NULL, NULL, NULL)
ON CONFLICT (code) DO NOTHING;
