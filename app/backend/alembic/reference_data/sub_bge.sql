CREATE TABLE IF NOT EXISTS reference_data.sub_bge (
    id                serial PRIMARY KEY,
    code              text NOT NULL UNIQUE,
    name              text NOT NULL,
    description       text,
    bge_id            integer NOT NULL REFERENCES reference_data.bge(id),
    entity_type       text NOT NULL DEFAULT 'sub_org' CHECK (entity_type IN ('sub_org', 'service_designee')),
    parent_sub_bge_id integer REFERENCES reference_data.sub_bge(id),
    onboarded         boolean NOT NULL DEFAULT false,
    cellular          text,
    data              text,
    voice             text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

INSERT INTO reference_data.sub_bge (code, name, bge_id, entity_type, onboarded, cellular, data, voice) VALUES
    ('Agriculture and Food',                          'Agriculture and Food',                          (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Attorney General',                              'Attorney General',                              (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Children and Family Development',               'Children and Family Development',               (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Citizens Services',                             'Citizens'' Services',                           (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'CSBC', 'CSBC', 'CSBC'),
    -- Education & Child Care is a ministry (sub-org) under Gov BC like any other,
    -- even though reports report it at BGE level. School-district spend reported
    -- under ECC is split out to the 'School Districts' BGE upstream; the remaining
    -- (ministry) ECC spend resolves to this sub_bge in int_service_spend_line_items.
    ('Education and Child Care',                      'Education and Child Care',                      (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Emergency Management and Climate Readiness',    'Emergency Management and Climate Readiness',    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Energy and Climate Solutions',                  'Energy and Climate Solutions',                  (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Environment and Parks',                         'Environment and Parks',                         (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Finance',                                       'Finance',                                       (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Forests',                                       'Forests',                                       (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Health',                                        'Health',                                        (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Housing and Municipal Affairs',                 'Housing and Municipal Affairs',                 (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Indigenous Relations and Reconciliation',       'Indigenous Relations and Reconciliation',       (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Infrastructure',                                'Infrastructure',                                (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Jobs Economic Development and Innovation',      'Jobs & Economic Growth',                        (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Labour',                                        'Labour',                                        (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Mining and Critical Minerals',                  'Mining and Critical Minerals',                  (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Post-Secondary Education and Future Skills',    'Post-Secondary Education and Future Skills',    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Public Safety and Solicitor General',           'Public Safety and Solicitor General',           (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Social Development and Poverty Reduction',      'Social Development and Poverty Reduction',      (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Tourism Arts Culture and Sport',                'Tourism Arts Culture and Sport',                (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Transportation and Transit',                    'Transportation and Transit',                    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Water Land and Resource Stewardship',           'Water Land and Resource Stewardship',           (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('Office of the Premier',                         'Office of the Premier',                         (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('BC Public Service Agency',                      'BC Public Service Agency',                      (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org', true, 'Self', 'CSBC', 'CSBC'),
    ('School District 5',    'School District 5 Southeast Kootenay',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 6',    'School District 6 Rocky Mountain',                      (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 8',    'School District 8 Kootenay Lake',                       (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 10',   'School District 10 Arrow Lakes',                        (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 19',   'School District 19 Revelstoke',                         (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 20',   'School District 20 Kootenay-Columbia',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 22',   'School District 22 Vernon',                             (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 23',   'School District 23 Central Okanagan',                   (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 27',   'School District 27 Cariboo-Chilcotin',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 28',   'School District 28 Quesnel',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 33',   'School District 33 Chilliwack',                         (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 34',   'School District 34 Abbotsford',                         (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 35',   'School District 35 Langley',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 36',   'School District 36 Surrey',                             (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 37',   'School District 37 Delta',                              (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 38',   'School District 38 Richmond',                           (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 39',   'School District 39 Vancouver',                          (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 40',   'School District 40 New Westminster',                    (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 41',   'School District 41 Burnaby',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 42',   'School District 42 Maple Ridge-Pitt Meadows',           (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 43',   'School District 43 Coquitlam',                          (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 44',   'School District 44 North Vancouver',                    (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 45',   'School District 45 West Vancouver',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 46',   'School District 46 Sunshine Coast',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 47',   'School District 47 qathet',                             (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 48',   'School District 48 Sea to Sky',                         (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 49',   'School District 49 Central Coast',                      (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 50',   'School District 50 Haida Gwaii',                        (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 51',   'School District 51 Boundary',                           (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 52',   'School District 52 Prince Rupert',                      (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 53',   'School District 53 Okanagan Similkameen',               (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 54',   'School District 54 Bulkley Valley',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 57',   'School District 57 Prince George',                      (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 58',   'School District 58 Nicola-Similkameen',                 (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 59',   'School District 59 Peace River South',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 60',   'School District 60 Peace River North',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 61',   'School District 61 Greater Victoria',                   (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 62',   'School District 62 Sooke',                              (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 63',   'School District 63 Saanich',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 64',   'School District 64 Gulf Islands',                       (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 67',   'School District 67 Okanagan Skaha',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 68',   'School District 68 Nanaimo-Ladysmith',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 69',   'School District 69 Qualicum',                           (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 70',   'School District 70 Pacific Rim',                        (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 71',   'School District 71 Comox Valley',                       (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 72',   'School District 72 Campbell River',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 73',   'School District 73 Kamloops/Thompson',                  (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 74',   'School District 74 Gold Trail',                         (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 75',   'School District 75 Mission',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 78',   'School District 78 Fraser-Cascade',                     (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 79',   'School District 79 Cowichan Valley',                    (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 81',   'School District 81 Fort Nelson',                        (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 82',   'School District 82 Coast Mountains',                    (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 83',   'School District 83 North Okanagan-Shuswap',             (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 84',   'School District 84 Vancouver Island West',              (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 85',   'School District 85 Vancouver Island North',             (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 87',   'School District 87 Stikine',                            (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 91',   'School District 91 Nechako Lakes',                      (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 92',   'School District 92 Nisga''a',                           (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self'),
    ('School District 93',   'School District 93 Conseil scolaire francophone',       (SELECT id FROM reference_data.bge WHERE code = 'School Districts'), 'service_designee', true, 'Self', 'ECC', 'Self')
ON CONFLICT (code) DO NOTHING;

-- Service-designees with a parent sub_org. Must follow the insert above so the
-- parent lookups can resolve. The Citizens Services designees are the
-- authoritative list. The code preserves the raw (often all-caps) source value
-- used for upstream matching; the name is the normal-case display label.
INSERT INTO reference_data.sub_bge (code, name, bge_id, entity_type, parent_sub_bge_id, onboarded, cellular, data, voice) VALUES
    ('BC Assessment',                                       'BC Assessment',                                       (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('BC LDB',                                              'BC Liquor Distribution Branch',                       (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('BC Family Maintenance Agency',                        'BC Family Maintenance Agency',                        (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'CSBC', 'Self'),
    ('BC Financial Services Authority',                     'BC Financial Services Authority',                     (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('BC Housing Management Commission',                    'BC Housing Management Commission',                    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('BC Office of Human Rights Commissioner',              'BC Office of Human Rights Commissioner',              (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'n/a',  'Self'),
    ('BC Pension',                                          'BC Pension',                                          (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('Community Living BC',                                 'Community Living BC',                                 (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'CSBC', 'CSBC'),
    ('Destination BC',                                      'Destination BC',                                      (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'CSBC'),
    ('Elections BC',                                        'Elections BC',                                        (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'CSBC', 'CSBC'),
    ('Forest Practice Board',                               'Forest Practices Board',                              (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('Islands Trust Conservancy',                           'Islands Trust Conservancy',                           (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), false, NULL,   NULL,   NULL),
    ('LEGISLATIVE ASSEMBLY',                                'Legislative Assembly',                                (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('OFFICE OF THE AUDITOR GENERAL OF B C',                'Office of the Auditor General of BC',                 (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('OFFICE OF THE INFORMATION & PRIVACY COMMISSIONER',    'Office of the Information & Privacy Commissioner',    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), false, NULL,   NULL,   NULL),
    ('OFFICE OF THE MERIT COMMISSIONER',                    'Office of the Merit Commissioner',                    (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), false, NULL,   NULL,   NULL),
    ('OFFICE OF THE OMBUDSPERSON',                          'Office of the Ombudsperson',                          (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), false, NULL,   NULL,   NULL),
    ('OFFICE OF THE POLICE COMPLAINT COMMISSIONER',         'Office of the Police Complaint Commissioner',         (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), false, NULL,   NULL,   NULL),
    ('OFFICE OF THE REPRESENTATIVE FOR CHILDREN AND YOUTH', 'Office of the Representative for Children and Youth', (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('Public Guardian and Trustee',                         'Public Guardian and Trustee',                         (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'Self', 'Self'),
    ('ROYAL B C MUSEUM',                                    'Royal BC Museum',                                     (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'CSBC', 'Self'),
    ('Superior Court Judiciary Branch',                     'Superior Court Judiciary Branch',                     (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'n/a',  'Self'),
    ('TI Corp',                                             'Transportation Investment Corp',                      (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'service_designee', (SELECT id FROM reference_data.sub_bge WHERE code = 'Citizens Services'), true,  'Self', 'CSBC', 'n/a'),
    -- PHSA service designees.
    ('BC Emergency Health Services',                        'BC Emergency Health Services (BC Ambulance)',         (SELECT id FROM reference_data.bge WHERE code = 'PHSA'), 'service_designee', NULL, true,  'PHSA', 'PHSA', 'PHSA'),
    ('BC Cancer Agency',                                    'BC Cancer Agency',                                    (SELECT id FROM reference_data.bge WHERE code = 'PHSA'), 'service_designee', NULL, true,  'PHSA', 'PHSA', 'PHSA'),
    ('BC Centre for Disease Control',                       'BC Centre for Disease Control',                       (SELECT id FROM reference_data.bge WHERE code = 'PHSA'), 'service_designee', NULL, true,  'PHSA', 'PHSA', 'PHSA'),
    ('BC Shared Health Services',                           'BC Shared Health Services',                           (SELECT id FROM reference_data.bge WHERE code = 'PHSA'), 'service_designee', NULL, true,  'PHSA', 'PHSA', 'PHSA'),
    ('Providence Health Care',                              'Providence Health Care Society',                      (SELECT id FROM reference_data.bge WHERE code = 'VCHA (+PHC)'), 'service_designee', NULL, true,  'PHSA', 'PHSA', 'PHSA'),
    ('Vancouver General Hospital',                          'Vancouver General Hospital',                          (SELECT id FROM reference_data.bge WHERE code = 'VCHA (+PHC)'), 'service_designee', NULL, true,  'Self', 'PHSA', 'Self'),
    ('Powertech',                                           'Powertech',                                      (SELECT id FROM reference_data.bge WHERE code = 'BC Hydro'), 'service_designee', NULL, true,  'Self', 'n/a',  'n/a'),
    ('Power Ex',                                            'Powerex',                                             (SELECT id FROM reference_data.bge WHERE code = 'BC Hydro'), 'service_designee', NULL, false, NULL,   NULL,   NULL)
ON CONFLICT (code) DO NOTHING;

comment on table reference_data.sub_bge is 'Sub-organizations and service designees below a BGE';
comment on column reference_data.sub_bge.id is 'Unique ID for the sub BGE';
comment on column reference_data.sub_bge.code is 'Unique code for the sub-bge, used to resolve aliases';
comment on column reference_data.sub_bge.name is 'Display name';
comment on column reference_data.sub_bge.description is 'Free-text Description of the sub-bge';
comment on column reference_data.sub_bge.bge_id is 'BGE this entity rolls up to';
comment on column reference_data.sub_bge.entity_type is 'sub_org or service_designee';
comment on column reference_data.sub_bge.parent_sub_bge_id is 'Parent sub BGE for a designee under a sub-org, else null';
comment on column reference_data.sub_bge.onboarded is 'Whether the entity has been onboarded to NGTA/TSMA';
comment on column reference_data.sub_bge.cellular is 'Who provides cellular service: Self, CSBC, ECC, PHSA or n/a';
comment on column reference_data.sub_bge.data is 'Who provides data service: Self, CSBC, ECC, PHSA or n/a';
comment on column reference_data.sub_bge.voice is 'Who provides voice service: Self, CSBC, ECC, PHSA or n/a';