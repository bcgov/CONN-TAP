#!/usr/bin/env python3
"""Build the Lambda dependency layer zip when missing or requirements changed."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Match aws_lambda_function runtime/architecture in main.tf (python3.12, x86_64).
LAMBDA_PYTHON = "3.12"
LAMBDA_PLATFORM = "manylinux2014_x86_64"
BUILD_STAMP_VERSION = f"py{LAMBDA_PYTHON}-{LAMBDA_PLATFORM}"


def main() -> None:
    query = json.load(sys.stdin)
    ingest_dir = Path(query["ingest_dir"])
    layer_zip = Path(query["layer_zip"])
    req_hash = query["requirements_hash"]
    req_file = ingest_dir / "requirements.txt"
    stamp = layer_zip.with_name(f"{layer_zip.name}.requirements-hash")
    build_key = f"{req_hash}:{BUILD_STAMP_VERSION}"

    needs_build = (
        not layer_zip.is_file()
        or not stamp.is_file()
        or stamp.read_text(encoding="utf-8").strip() != build_key
    )

    if needs_build:
        layer_zip.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "python"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--requirement",
                    str(req_file),
                    "--target",
                    str(target),
                    "--platform",
                    LAMBDA_PLATFORM,
                    "--python-version",
                    LAMBDA_PYTHON,
                    "--implementation",
                    "cp",
                    "--only-binary",
                    ":all:",
                    "--no-cache-dir",
                    "--quiet",
                ],
                check=True,
            )
            layer_zip.unlink(missing_ok=True)
            with zipfile.ZipFile(layer_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in target.rglob("*"):
                    if path.is_file():
                        zf.write(path, Path("python") / path.relative_to(target))

        stamp.write_text(build_key, encoding="utf-8")

    json.dump(
        {"built": str(needs_build).lower(), "layer_zip": str(layer_zip)},
        sys.stdout,
    )


if __name__ == "__main__":
    main()
