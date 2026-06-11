CREATE SCHEMA IF NOT EXISTS reference_data;

CREATE TABLE IF NOT EXISTS reference_data.sector (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_data.provider (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_data.bge (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    sector_id   integer NOT NULL REFERENCES reference_data.sector(id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_data.service_id (
    id               serial PRIMARY KEY,
    source_system    text NOT NULL,
    provider_id      integer NOT NULL REFERENCES reference_data.provider(id),
    code             text NOT NULL,
    service_category text NOT NULL,
    service_name     text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_system, code)
);

CREATE TABLE IF NOT EXISTS reference_data.service_tower (
    id               serial PRIMARY KEY,
    source_system    text NOT NULL,
    provider_id      integer NOT NULL REFERENCES reference_data.provider(id),
    code             text NOT NULL,
    service_category text NOT NULL,
    service_name     text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_system, code)
);

INSERT INTO reference_data.sector (code, name) VALUES
    ('health_authorities', 'Health Authorities'),
    ('crown_corporations', 'Crown Corporations'),
    ('school_districts',   'School Districts'),
    ('gov_ecc',            'Gov & ECC')
ON CONFLICT (code) DO NOTHING;

INSERT INTO reference_data.provider (code, name) VALUES
    ('telus',  'TELUS'),
    ('rogers', 'Rogers')
ON CONFLICT (code) DO NOTHING;

INSERT INTO reference_data.service_id (source_system, provider_id, code, service_category, service_name)
SELECT 'ngta', p.id, svc.code, svc.service_category, svc.service_name
FROM (VALUES
    ('164',  'Cellular', 'Wireless Cellular'),
    ('130',  'Cellular', 'Wireless Cellular'),
    ('1001', 'Data',     'Wireline Data'),
    ('103',  'Data',     'Wireline Data'),
    ('104',  'Voice',    'Wireline Voice'),
    ('102',  'Voice',    'Wireline Voice'),
    ('106',  'Voice',    'Wireline Voice')
) AS svc(code, service_category, service_name)
JOIN reference_data.provider p ON p.code = 'telus'
ON CONFLICT (source_system, code) DO NOTHING;

INSERT INTO reference_data.service_tower (source_system, provider_id, code, service_category, service_name)
SELECT 'tsma', p.id, svc.code, svc.service_category, svc.service_name
FROM (VALUES
    ('business internet', 'Data',                        'Business Internet'),
    ('data - wan',        'Data',                        'WAN Data'),
    ('conferencing',      'Voice',                       'Conferencing'),
    ('long distance',     'Voice',                       'Long Distance'),
    ('voice',             'Voice',                       'Voice'),
    ('managed wlan',      'Other Professional Services', 'Managed WLAN')
) AS svc(code, service_category, service_name)
JOIN reference_data.provider p ON p.code = 'telus'
ON CONFLICT (source_system, code) DO NOTHING;

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
