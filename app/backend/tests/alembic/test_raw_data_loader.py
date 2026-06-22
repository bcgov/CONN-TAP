from unittest.mock import MagicMock, patch

import alembic.raw_data_loader as loader


def test_raw_data_sql_dir_exists() -> None:
    assert loader.RAW_DATA_SQL_DIR.is_dir()


def test_raw_data_schema_files_is_non_empty_tuple() -> None:
    assert isinstance(loader.RAW_DATA_SCHEMA_FILES, tuple)
    assert len(loader.RAW_DATA_SCHEMA_FILES) > 0


def test_execute_raw_data_sql_files_delegates() -> None:
    with patch("alembic.raw_data_loader.execute_sql_files") as mock_exec:
        loader.execute_raw_data_sql_files()
        mock_exec.assert_called_once_with(loader.RAW_DATA_SQL_DIR, loader.RAW_DATA_SCHEMA_FILES)


def test_drop_raw_data_schema_calls_op_execute() -> None:
    mock_op = MagicMock()
    with patch("alembic.raw_data_loader.op", mock_op):
        loader.drop_raw_data_schema()
        mock_op.execute.assert_called_once_with("DROP SCHEMA IF EXISTS raw_data CASCADE")
