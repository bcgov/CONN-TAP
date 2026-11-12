#!/usr/bin/env python3
"""Keep English Statement Category labels across all tabs of a TELUS workbook."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import tempfile

from openpyxl import load_workbook


_CATEGORY = re.compile(r"eng&&(.+?)&&fr-ca&&.*&&", re.IGNORECASE | re.DOTALL)


def clean_category(value: str) -> str:
    """Extract English from TELUS bilingual labels; preserve ordinary text."""
    stripped = value.strip()
    match = _CATEGORY.fullmatch(stripped)
    if match:
        english = match.group(1).strip()
        if not english or "&&" in english:
            raise ValueError(f"Malformed TELUS category: {value!r}")
        return english
    if "eng&&" in stripped.lower() or "fr-ca&&" in stripped.lower():
        raise ValueError(f"Malformed TELUS category: {value!r}")
    return value


def is_category_header(value: object) -> bool:
    return isinstance(value, str) and re.sub(
        r"[\s_-]+", "", value
    ).casefold() == "statementcategory"


def clean_workbook(source: Path, output: Path) -> list[tuple[str, int | None]]:
    """Write a new workbook, returning changed-cell counts (None for skipped tabs)."""
    if source.suffix.lower() != ".xlsx" or output.suffix.lower() != ".xlsx":
        raise ValueError("Input and output must be .xlsx files.")
    if source.resolve() == output.resolve():
        raise ValueError("Output must differ from the input; the original is preserved.")
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")

    workbook = load_workbook(source, data_only=False)
    results: list[tuple[str, int | None]] = []
    try:
        for sheet in workbook.worksheets:
            columns: set[int] = set()
            changed = 0
            for row in sheet.iter_rows():
                for cell in row:
                    if is_category_header(cell.value):
                        columns.add(cell.column)
                    elif cell.column in columns and cell.data_type != "f":
                        value = cell.value
                        if not isinstance(value, str):
                            continue
                        try:
                            cleaned = clean_category(value)
                        except ValueError as exc:
                            raise ValueError(
                                f"{sheet.title}!{cell.coordinate}: {exc}"
                            ) from exc
                        if cleaned != value:
                            cell.value = cleaned
                            # Category labels are text, even if they start with "=".
                            cell.data_type = "s"
                            changed += 1
            results.append((sheet.title, changed if columns else None))

        if all(count is None for _, count in results):
            raise ValueError("No Statement Category column found in any worksheet.")

        # Publish only a fully saved workbook, without replacing an existing file.
        with tempfile.TemporaryDirectory(dir=output.parent) as temp_dir:
            temporary = Path(temp_dir) / "cleaned.xlsx"
            workbook.save(temporary)
            os.link(temporary, output)
    finally:
        workbook.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="TELUS .xlsx report")
    parser.add_argument(
        "-o", "--output", type=Path,
        help="New .xlsx path (default: <input>_cleaned.xlsx)",
    )
    args = parser.parse_args()
    output = args.output or args.input.with_name(f"{args.input.stem}_cleaned.xlsx")
    try:
        results = clean_workbook(args.input, output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    for title, count in results:
        if count is None:
            print(f"{title}: SKIPPED (no Statement Category column)")
        else:
            print(f"{title}: {count} categories cleaned")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
