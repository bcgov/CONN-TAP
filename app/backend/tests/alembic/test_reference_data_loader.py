from unittest.mock import MagicMock, patch

import alembic.reference_data_loader as loader


def test_reference_data_sql_dir_exists() -> None:
    assert loader.REFERENCE_DATA_SQL_DIR.is_dir()


def test_reference_data_schema_files_is_non_empty_tuple() -> None:
    assert isinstance(loader.REFERENCE_DATA_SCHEMA_FILES, tuple)
    assert len(loader.REFERENCE_DATA_SCHEMA_FILES) > 0


def test_execute_reference_data_sql_files_delegates() -> None:
    with patch("alembic.reference_data_loader.execute_sql_files") as mock_exec:
        loader.execute_reference_data_sql_files()
        mock_exec.assert_called_once_with(loader.REFERENCE_DATA_SQL_DIR, loader.REFERENCE_DATA_SCHEMA_FILES)


def test_drop_reference_data_schema_calls_op_execute() -> None:
    mock_op = MagicMock()
    with patch("alembic.reference_data_loader.op", mock_op):
        loader.drop_reference_data_schema()
        mock_op.execute.assert_called_once_with("DROP SCHEMA IF EXISTS reference_data CASCADE")
