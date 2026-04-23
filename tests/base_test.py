from pathlib import Path
import importlib.util
import sys
import types


def test_telus_extract_params_from_key(monkeypatch) -> None:
    spec = importlib.util.spec_from_file_location(
        "lambda_ngta_telus_test",
        Path("lambda/lambda_ngta_telus.py"),
    )
    module = importlib.util.module_from_spec(spec)

    monkeypatch.setitem(
        sys.modules,
        "boto3",
        types.SimpleNamespace(
            client=lambda _name: types.SimpleNamespace(start_job_run=lambda **_kwargs: {})
        ),
    )
    monkeypatch.setenv("GLUE_JOB_NAME", "test-job")
    spec.loader.exec_module(module)

    assert module.extract_params_from_key(
        "raw/telus/spend_reports/2025/December/December 2025 Consolidated Spend Report.xlsx"
    ) == ("2025", "December", "12")
