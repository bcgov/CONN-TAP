"""Rename two service categories, add Unknown, and move six service codes.

Revision ID: 005_time_limited_services
Revises: 004_reference_data_schema
Create Date: 2026-08-05

The 004 seed files stay as the original snapshot; the reference data moves
forward here, so a fresh database (004 seeds, then this) and an already-seeded
one land in the same place.

  Temporary Services          -> Time Limited Services
  Other Professional Services -> Professional Services
  (new)                       -> Unknown

  IVR              -> Voice
  MMS              -> Cellular
  Managed WLAN     -> Time Limited Services
  Managed Security -> Time Limited Services
  Managed Router   -> Time Limited Services
  Rogers 'other'   -> Unknown

The rogers 'other' code is the fallback for rows with no productline (late fees,
credit memos and the like) — spend we can't attribute to a real service. It moves
out of Professional Services into its own Unknown category, leaving Professional
Services empty until something is mapped into it.

The renames are UPDATEs, so the category ids survive and analytics rows keep
pointing at them. The fact table stores the resolved service_category_id though,
so the marts need a dbt run for existing spend to move; the renames alone don't.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "005_time_limited_services"
down_revision: Union[str, None] = "004_reference_data_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename before remapping — three of the moves below target
    # time_limited_services, which doesn't exist until this runs.
    op.execute(
        """
        UPDATE reference_data.service_category
        SET code = 'time_limited_services', name = 'Time Limited Services', updated_at = now()
        WHERE code = 'temporary_services'
        """
    )
    op.execute(
        """
        UPDATE reference_data.service_category
        SET code = 'professional_services', name = 'Professional Services', updated_at = now()
        WHERE code = 'other_professional_services'
        """
    )
    op.execute(
        """
        INSERT INTO reference_data.service_category (code, name) VALUES ('unknown', 'Unknown')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(_remap("voice", "('tsma', 'ivr')"))
    op.execute(_remap("cellular", "('tsma', 'mms')"))
    op.execute(
        _remap(
            "time_limited_services",
            "('tsma', 'managed wlan'), ('tsma_other', 'managed_security'),"
            " ('tsma_other', 'managed_router')",
        )
    )
    op.execute(_remap("unknown", "('ngta', 'other')"))


def downgrade() -> None:
    op.execute(
        """
        UPDATE reference_data.service_category
        SET code = 'temporary_services', name = 'Temporary Services', updated_at = now()
        WHERE code = 'time_limited_services'
        """
    )
    op.execute(
        """
        UPDATE reference_data.service_category
        SET code = 'other_professional_services', name = 'Other Professional Services',
            updated_at = now()
        WHERE code = 'professional_services'
        """
    )
    op.execute(_remap("temporary_services", "('tsma', 'ivr'), ('tsma', 'mms')"))
    op.execute(
        _remap(
            "other_professional_services",
            "('tsma', 'managed wlan'), ('tsma_other', 'managed_security'),"
            " ('tsma_other', 'managed_router'), ('ngta', 'other')",
        )
    )
    # Only droppable once nothing points at it, so this trails the remaps. Any
    # analytics rows still referencing it need a dbt run to move off first.
    op.execute("DELETE FROM reference_data.service_category WHERE code = 'unknown'")


def _remap(category_code: str, source_code_pairs: str) -> str:
    """Point the given (source_system, code) service codes at a category.

    Both arguments are literals written in this file — no external input.
    """
    return f"""
        UPDATE reference_data.service_code sc
        SET service_category_id = cat.id, updated_at = now()
        FROM reference_data.service_category cat
        WHERE cat.code = '{category_code}'
          AND (sc.source_system, sc.code) IN ({source_code_pairs})
    """
