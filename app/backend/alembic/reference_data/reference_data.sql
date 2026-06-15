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

CREATE TABLE IF NOT EXISTS reference_data.service_category (
    id          serial PRIMARY KEY,
    code        text NOT NULL UNIQUE,
    name        text NOT NULL,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_data.service_code (
    id                  serial PRIMARY KEY,
    source_system       text NOT NULL,
    provider_id         integer NOT NULL REFERENCES reference_data.provider(id),
    code                text NOT NULL,
    service_category_id integer NOT NULL REFERENCES reference_data.service_category(id),
    service_name        text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_system, code)
);

INSERT INTO reference_data.sector (code, name) VALUES
    ('health_authorities', 'Health Authorities'),
    ('crown_corporations', 'Crown Corporations'),
    ('school_districts',   'School Districts'),
    ('gov_ecc',            'Gov & ECC')
ON CONFLICT (code) DO NOTHING;

INSERT INTO reference_data.service_category (code, name) VALUES
    ('cellular',                    'Cellular'),
    ('data',                        'Data'),
    ('voice',                       'Voice'),
    ('temporary_services',          'Temporary Services'),
    ('other_professional_services', 'Other Professional Services')
ON CONFLICT (code) DO NOTHING;

INSERT INTO reference_data.provider (code, name) VALUES
    ('telus',  'TELUS'),
    ('rogers', 'Rogers')
ON CONFLICT (code) DO NOTHING;

INSERT INTO reference_data.service_code (source_system, provider_id, code, service_category_id, service_name)
SELECT svc.source_system, p.id, svc.code, sc.id, svc.service_name
FROM (VALUES
    -- ngta: numeric service IDs
    ('ngta', 'telus', '164',               'cellular',                    'Wireless Cellular'),
    ('ngta', 'telus', '130',               'cellular',                    'Wireless Cellular'),
    ('ngta', 'telus', '1001',              'data',                        'Wireline Data'),
    ('ngta', 'telus', '103',               'data',                        'Wireline Data'),
    ('ngta', 'telus', '104',               'voice',                       'Wireline Voice'),
    ('ngta', 'telus', '102',               'voice',                       'Wireline Voice'),
    ('ngta', 'telus', '106',               'voice',                       'Wireline Voice'),
    -- ngta: fallback (rows with no numeric source_service_id)
    ('ngta', 'telus', 'wireless',          'cellular',                    'Wireless'),
    -- tsma: service tower values (wireline rows)
    ('tsma', 'telus', 'business internet', 'data',                        'Business Internet'),
    ('tsma', 'telus', 'data - wan',        'data',                        'WAN Data'),
    ('tsma', 'telus', 'conferencing',      'voice',                       'Conferencing'),
    ('tsma', 'telus', 'long distance',     'voice',                       'Long Distance'),
    ('tsma', 'telus', 'voice',             'voice',                       'Voice'),
    ('tsma', 'telus', 'managed wlan',      'other_professional_services', 'Managed WLAN'),
    -- tsma: fallbacks (wireless/ivr/mms rows have no tower)
    ('tsma', 'telus', 'wireless',          'cellular',                    'Wireless'),
    ('tsma', 'telus', 'ivr',               'temporary_services',          'IVR'),
    ('tsma', 'telus', 'mms',               'temporary_services',          'MMS'),
    -- tsma_other: always other professional services
    ('tsma_other', 'telus', 'managed_security', 'other_professional_services', 'Managed Security'),
    ('tsma_other', 'telus', 'managed_router',   'other_professional_services', 'Managed Router'),
    -- rogers: productline values
    ('rogers', 'rogers', 'cellular',       'cellular',                    'Cellular'),
    ('rogers', 'rogers', 'data',           'data',                        'Data'),
    ('rogers', 'rogers', 'voice',          'voice',                       'Voice'),
    ('rogers', 'rogers', 'business voice', 'voice',                       'Business Voice'),
    ('rogers', 'rogers', 'cable gateway',  'data',                        'Cable Gateway')
) AS svc(source_system, provider_code, code, service_category_code, service_name)
JOIN reference_data.provider p ON p.code = svc.provider_code
JOIN reference_data.service_category sc ON sc.code = svc.service_category_code
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
