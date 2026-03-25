from pathlib import Path
import importlib.util
import sys
import types


# a dummy test
def test_readme_exists() -> None:
    assert Path("README.md").exists()


def test_tsma_qsr_parse_key() -> None:
    spec = importlib.util.spec_from_file_location(
        "lambda_tsma_qsr_test",
        Path("lambda/lambda_tsma_qsr.py"),
    )
    module = importlib.util.module_from_spec(spec)

    original_boto3 = sys.modules.get("boto3")
    sys.modules["boto3"] = types.SimpleNamespace(
        client=lambda _name: types.SimpleNamespace(start_job_run=lambda **_kwargs: {})
    )

    try:
        spec.loader.exec_module(module)
    finally:
        if original_boto3 is None:
            del sys.modules["boto3"]
        else:
            sys.modules["boto3"] = original_boto3

    assert module._parse_key("raw_quarterly_spend_report/2025/Q1/wln/Data_Voice.xlsx") == (
        "2025",
        "Q1",
        "wln",
        "Data_Voice.xlsx",
    )
