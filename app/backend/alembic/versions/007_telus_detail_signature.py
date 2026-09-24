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

The body lives in reference_data/telus_functions.sql, a file of its own so
this migration can replay it and nothing else. functions.sql cannot be
replayed on a live database -- it ends with a DROP of raw_data.norm_key,
which Postgres refuses once the Rogers cellular validation view depends on
it -- so the Telus function is kept apart from it.
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
    _loader.execute_reference_data_files("telus_functions.sql")


def downgrade() -> None:
    # Both functions upgrade() installs, predicate first: its body calls the
    # signature, so dropping the signature first would leave it briefly broken.
    #
    # CASCADE because intermediate.int_telus_ngta_spend is a view whose definition
    # calls the signature, and Postgres refuses to drop a function a view depends on.
    # Without it this downgrade fails by default on any database where dbt has run.
    # What CASCADE takes is only dbt-built views -- nothing else references these --
    # and `dbt run` rebuilds them, which a downgrade needs anyway because the models
    # at the matching revision no longer call the function.
    op.execute("DROP FUNCTION IF EXISTS reference_data.telus_is_hardware_detail(text) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS reference_data.telus_detail_signature(text) CASCADE")
