import sys
import types

import alembic

# Inject a mock op
_mock_op = types.ModuleType("alembic.op")
alembic.op = _mock_op
sys.modules["alembic.op"] = _mock_op

# Mock sqlalchemy
if "sqlalchemy" not in sys.modules:
    _mock_sa = types.ModuleType("sqlalchemy")
    _mock_sa.text = lambda s: s
    sys.modules["sqlalchemy"] = _mock_sa
