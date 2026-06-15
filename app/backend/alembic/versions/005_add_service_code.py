"""Merge 003 branches and add reference_data.service_code table.

Revision ID: 005_add_service_code
Revises: 003_datasets_registry, 003_reference_data_schema
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_add_service_code"
down_revision: Union[str, Sequence[str], None] = (
    "003_datasets_registry",
    "003_reference_data_schema",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
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
        )
    """)

    op.execute("""
        INSERT INTO reference_data.service_code
            (source_system, provider_id, code, service_category_id, service_name)
        SELECT svc.source_system, p.id, svc.code, sc.id, svc.service_name
        FROM (VALUES
            ('ngta',       'telus',   '164',               'cellular',                    'Wireless Cellular'),
            ('ngta',       'telus',   '130',               'cellular',                    'Wireless Cellular'),
            ('ngta',       'telus',   '1001',              'data',                        'Wireline Data'),
            ('ngta',       'telus',   '103',               'data',                        'Wireline Data'),
            ('ngta',       'telus',   '104',               'voice',                       'Wireline Voice'),
            ('ngta',       'telus',   '102',               'voice',                       'Wireline Voice'),
            ('ngta',       'telus',   '106',               'voice',                       'Wireline Voice'),
            ('ngta',       'telus',   'wireless',          'cellular',                    'Wireless'),
            ('tsma',       'telus',   'business internet', 'data',                        'Business Internet'),
            ('tsma',       'telus',   'data - wan',        'data',                        'WAN Data'),
            ('tsma',       'telus',   'conferencing',      'voice',                       'Conferencing'),
            ('tsma',       'telus',   'long distance',     'voice',                       'Long Distance'),
            ('tsma',       'telus',   'voice',             'voice',                       'Voice'),
            ('tsma',       'telus',   'managed wlan',      'other_professional_services', 'Managed WLAN'),
            ('tsma',       'telus',   'wireless',          'cellular',                    'Wireless'),
            ('tsma',       'telus',   'ivr',               'temporary_services',          'IVR'),
            ('tsma',       'telus',   'mms',               'temporary_services',          'MMS'),
            ('tsma_other', 'telus',   'managed_security',  'other_professional_services', 'Managed Security'),
            ('tsma_other', 'telus',   'managed_router',    'other_professional_services', 'Managed Router'),
            ('rogers',     'rogers',  'cellular',          'cellular',                    'Cellular'),
            ('rogers',     'rogers',  'data',              'data',                        'Data'),
            ('rogers',     'rogers',  'voice',             'voice',                       'Voice'),
            ('rogers',     'rogers',  'business voice',    'voice',                       'Business Voice'),
            ('rogers',     'rogers',  'cable gateway',     'data',                        'Cable Gateway')
        ) AS svc(source_system, provider_code, code, service_category_code, service_name)
        JOIN reference_data.provider p ON p.code = svc.provider_code
        JOIN reference_data.service_category sc ON sc.code = svc.service_category_code
        ON CONFLICT (source_system, code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reference_data.service_code")
