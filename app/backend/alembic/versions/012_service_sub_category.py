"""Bring the service categories in line with the analysts' list: TLS sub-categories and Ancillary Products.

Revision ID: 012_service_sub_category
Revises: 011_rogers_professional_services
Create Date: 2026-10-27

Some categories split further: Time Limited Services is billed as Centrex, Analog
Private Line, Copper and so on. Sub-categories get their own table, each row pointing
at its category, so reports that list service_category are not affected.

The TLS rows are the analysts' list: the tabs of the LTO list plus SIPA. bill_type is
the bill each one shows up on (Voice, Data or Cellular).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012_service_sub_category"
down_revision: Union[str, None] = "011_rogers_professional_services"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reference_data.service_sub_category (
            id                  serial PRIMARY KEY,
            service_category_id integer NOT NULL REFERENCES reference_data.service_category (id),
            code                text NOT NULL UNIQUE,
            name                text NOT NULL,
            bill_type           text,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        INSERT INTO reference_data.service_sub_category (service_category_id, code, name, bill_type)
        SELECT sc.id, v.code, v.name, v.bill_type
        FROM reference_data.service_category sc
        CROSS JOIN (VALUES
            ('tls_sipa',                       'SIPA',                                'Cellular'),
            ('tls_centrex',                    'Centrex',                             'Voice'),
            ('tls_analog_private_line',        'Analog Private Line',                 'Voice'),
            ('tls_copper',                     'Copper Based Services',               'Voice'),
            ('tls_health_grade_managed_voice', 'Health Grade Managed Voice',          'Voice'),
            ('tls_adsl_voice',                 'ADSL Services on Voice Bill',         'Voice'),
            ('tls_ip_trunking_r2',             'IP Trunking R2',                      'Voice'),
            ('tls_adsl_data',                  'ADSL/BI/Office Internet - Data Bill', 'Data'),
            ('tls_managed_router',             'Managed Router',                      'Data'),
            ('tls_optical_ethernet',           'Carrier Optical Ethernet',            'Data'),
            ('tls_managed_wlan',               'Managed WLAN',                        'Data')
        ) AS v (code, name, bill_type)
        WHERE sc.code = 'time_limited_services'
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO reference_data.service_category (code, name)
        VALUES ('ancillary_hardware', 'Ancillary Products - Hardware')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(_rename("cellular_hardware", "Ancillary Products - Cellular Hardware"))
    op.execute(_rename("professional_services", "Ancillary Products - Professional Services"))


def downgrade() -> None:
    op.execute(_rename("cellular_hardware", "Cellular Hardware"))
    op.execute(_rename("professional_services", "Professional Services"))
    # Only droppable once nothing points at it: analytics rows still using it
    # need a dbt run to move off first.
    op.execute("DELETE FROM reference_data.service_category WHERE code = 'ancillary_hardware'")
    op.execute("DROP TABLE IF EXISTS reference_data.service_sub_category")


def _rename(category_code: str, name: str) -> str:
    """Set a category's display name. Both arguments are literals written in this file."""
    return f"""
        UPDATE reference_data.service_category
        SET name = '{name}', updated_at = now()
        WHERE code = '{category_code}'
    """
