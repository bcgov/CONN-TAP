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
    -- rogers: productline values (rogers data comes through ngta portal)
    ('ngta', 'rogers', 'cellular',       'cellular',                    'Cellular'),
    ('ngta', 'rogers', 'data',           'data',                        'Data'),
    ('ngta', 'rogers', 'voice',          'voice',                       'Voice'),
    ('ngta', 'rogers', 'business voice', 'voice',                       'Business Voice'),
    ('ngta', 'rogers', 'cable gateway',  'data',                        'Cable Gateway'),
    -- rogers: fallback for rows with no productline (eg: late fees, credit memos)
    ('ngta', 'rogers', 'other',          'other_professional_services', 'Other')
) AS svc(source_system, provider_code, code, service_category_code, service_name)
JOIN reference_data.provider p ON p.code = svc.provider_code
JOIN reference_data.service_category sc ON sc.code = svc.service_category_code
ON CONFLICT (source_system, code) DO NOTHING;
