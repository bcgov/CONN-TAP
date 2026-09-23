"""Add reference_data.telus_detail_signature, the Telus hardware-matching key.

Revision ID: 007_telus_detail_signature
Revises: 006_telus_164_cellular_hardware
Create Date: 2026-09-23

Telus writes the financed amount, the term and the expiry date into the
detail_description itself, so the same charge arrives under many spellings
('Easy Payment $27.50 - 2yrs (exp. Mar 2027)', 'Easy Payment $40.00 - 3 yrs
(exp. Jan 2028)'). Matching those literally would need a new allowlist entry
every month, so int_telus_ngta_spend matches the seeded hardware list on the
description's word signature instead. This adds the function that produces it.

The body lives in reference_data/functions.sql -- every statement there is
CREATE OR REPLACE or DROP IF EXISTS, so re-running the file is the whole
migration and the definition stays in one place.
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

from alembic import op

_loader_path = Path(__file__).resolve().parent.parent / "reference_data_loader.py"
_spec = importlib.util.spec_from_file_location("migration_reference_data_loader", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_loader)

revision: str = "007_telus_detail_signature"
down_revision: Union[str, None] = "006_telus_164_cellular_hardware"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _loader.execute_reference_data_functions()


def downgrade() -> None:
    # int_telus_ngta_spend calls this, and Postgres refuses to drop a function a
    # view depends on, so the marts have to be rebuilt off it first -- check out
    # the matching model revision and `dbt run` before downgrading.
    op.execute("DROP FUNCTION IF EXISTS reference_data.telus_detail_signature(text)")
