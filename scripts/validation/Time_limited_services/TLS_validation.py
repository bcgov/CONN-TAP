"""
TELUS Time Limited Services (TLS) discovery and categorization.

Current inputs:
  - September 2026 Consolidated Spend report.xlsx
  - Data Services TSMA and NGTA - all BGEs September 2026_v6 - Copy.xlsx
      Sheet: LTO List
      Required columns:
        - Charge Description
        - TLS Category
  - account_description_mapping.xlsx

Removed input:
  - Limited Time Onboarded Services - Consolidated.xlsx

Output:
  - TLS_Aug_2026_new.xlsx

The output contains:
  - Summary worksheet
  - One worksheet per BGE
  - Only exact TLS matches with a score of 100

TLS descriptions and categories are both taken directly from the LTO List.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from rapidfuzz import fuzz, process

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    from difflib import SequenceMatcher

    RAPIDFUZZ_AVAILABLE = False


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
DATA_DIR = Path(
    r"C:\Users\AFATHALI\OneDrive - Government of BC"
    r"\Documents\Time_limited services"
)

REPORT_FILES = {
    "2026-09": DATA_DIR / "August 2026 Consolidated Spend report.xlsx",
}

TLS_SOURCE_FILE = (
    DATA_DIR
    / "Data Services with TLS LTO Comparison.xlsx"
)

TLS_SOURCE_SHEET = "LTO List"

ACCOUNT_MAPPING_FILE = DATA_DIR / "account_description_mapping.xlsx"

OUTPUT_FILE = DATA_DIR / "TLS_Aug_2026_new.xlsx"

# Fuzzy matches can still be calculated for review purposes, but the final
# output only includes exact matches with a score of 100.
TLS_FUZZY_THRESHOLD = 92

# When True, only services observed in the latest report month are included.
ONLY_CURRENT_SERVICES = True


REPORT_COLUMN_ALIASES = {
    "account_number": [
        "Account Number",
        "BAN",
        "Ban",
    ],
    "account_description": [
        "Account Description",
        "Billing Name",
        "Account Name",
    ],
    "service_number": [
        "Service Number",
        "Service ID",
        "Subscriber #",
    ],
    "detail_description": [
        "Detail Description",
        "Charge Description",
        "Service Description",
    ],
    "amount": [
        "Amount",
        "Charge",
        "Current Charge",
        "TSMA Total $",
    ],
    "service_address": [
        "Service Address",
        "Service Location",
        "Circuit Address",
    ],
    "organization": [
        "Organization",
        "Corporation Name",
        "BGE",
    ],
    "statement_date": [
        "Statement Date",
        "Month",
    ],
}


# -----------------------------------------------------------------------------
# TEXT AND MATCHING HELPERS
# -----------------------------------------------------------------------------
def normalize_text(value) -> str:
    """
    Create a conservative comparison key without changing word meaning.

    This function:
      - Converts text to uppercase
      - Removes accents
      - Removes asterisks
      - Replaces punctuation with spaces
      - Standardizes whitespace
    """
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = html.unescape(text)
    text = text.upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"\*+", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_account_name(value) -> str:
    """
    Normalize Account Description values for exact account mapping.
    """
    if value is None or pd.isna(value):
        return ""

    text = html.unescape(str(value))

    text = (
        text.replace("\u00A0", " ")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
        .replace("—", "-")
        .replace("Â–", "-")
        .replace("Â", " ")
    )

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = text.upper()
    text = re.sub(r"\s+AND\s+", " & ", text)
    text = re.sub(r'["\']', "", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_value(value) -> str:
    """
    Convert a value to a stripped string.

    Blank values and pandas missing values become empty strings.
    """
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def find_column(
    columns: Iterable,
    aliases: list[str],
) -> str | None:
    """
    Find the first matching column from a list of possible aliases.

    Matching is case-insensitive and ignores leading or trailing spaces.
    """
    actual_columns = {
        str(column).strip().casefold(): column
        for column in columns
    }

    for alias in aliases:
        found_column = actual_columns.get(
            alias.strip().casefold()
        )

        if found_column is not None:
            return found_column

    return None


def best_match(
    query: str,
    choices: list[str],
) -> tuple[str, float]:
    """
    Return the best fuzzy match and its score.

    RapidFuzz is used when installed. Otherwise, difflib is used.
    """
    if not query or not choices:
        return "", 0.0

    if RAPIDFUZZ_AVAILABLE:
        result = process.extractOne(
            query,
            choices,
            scorer=fuzz.WRatio,
        )

        if result:
            return result[0], float(result[1])

        return "", 0.0

    best_choice = max(
        choices,
        key=lambda choice: SequenceMatcher(
            None,
            query,
            choice,
        ).ratio(),
    )

    score = (
        SequenceMatcher(
            None,
            query,
            best_choice,
        ).ratio()
        * 100
    )

    return best_choice, score


def safe_sheet_name(
    name: str,
    used: set[str],
) -> str:
    """
    Create a valid and unique Excel worksheet name.
    """
    cleaned = re.sub(
        r"[\\/*?:\[\]]",
        " ",
        clean_value(name),
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    if not cleaned:
        cleaned = "UNKNOWN BGE"

    base_name = cleaned[:31]
    candidate = base_name
    counter = 2

    while candidate.casefold() in used:
        suffix = f" {counter}"

        candidate = (
            base_name[: 31 - len(suffix)]
            + suffix
        )

        counter += 1

    used.add(candidate.casefold())

    return candidate


def first_nonblank(series: pd.Series) -> str:
    """
    Return the first nonblank value from a pandas Series.
    """
    for value in series:
        text = clean_value(value)

        if text:
            return text

    return ""


def joined_unique(series: pd.Series) -> str:
    """
    Return unique nonblank Series values as a comma-separated string.
    """
    values = []
    seen = set()

    for value in series:
        text = clean_value(value)

        if text and text not in seen:
            seen.add(text)
            values.append(text)

    return ", ".join(values)


# -----------------------------------------------------------------------------
# LOAD ACCOUNT DESCRIPTION MAPPING
# -----------------------------------------------------------------------------
def load_account_description_mapping() -> dict[str, str]:
    """
    Load Account Description mappings from Excel or CSV.

    Required columns:
      - raw_name
      - sub_bge_alias
    """
    if not ACCOUNT_MAPPING_FILE.exists():
        raise FileNotFoundError(
            "Account Description mapping file was not found:\n"
            f"  {ACCOUNT_MAPPING_FILE}"
        )

    extension = ACCOUNT_MAPPING_FILE.suffix.lower()

    if extension in {".xlsx", ".xls"}:
        mapping_df = pd.read_excel(
            ACCOUNT_MAPPING_FILE,
            sheet_name=0,
            dtype=str,
            keep_default_na=False,
        )

    elif extension == ".csv":
        mapping_df = pd.read_csv(
            ACCOUNT_MAPPING_FILE,
            dtype=str,
            encoding="utf-8-sig",
            comment="#",
            keep_default_na=False,
        )

    else:
        raise ValueError(
            f"Unsupported account mapping file type: {extension}. "
            "Use .xlsx, .xls, or .csv."
        )

    mapping_df.columns = [
        str(column).strip()
        for column in mapping_df.columns
    ]

    required_columns = {
        "raw_name",
        "sub_bge_alias",
    }

    missing_columns = (
        required_columns
        - set(mapping_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "The account mapping file is missing required column(s): "
            + ", ".join(sorted(missing_columns))
            + "\nColumns found: "
            + ", ".join(mapping_df.columns)
        )

    mapping_df["raw_name"] = (
        mapping_df["raw_name"]
        .astype(str)
        .str.strip()
    )

    mapping_df["sub_bge_alias"] = (
        mapping_df["sub_bge_alias"]
        .astype(str)
        .str.strip()
    )

    mapping_df = mapping_df[
        mapping_df["raw_name"].ne("")
        & mapping_df["sub_bge_alias"].ne("")
    ].copy()

    mapping_df["ACCOUNT_DESCRIPTION_KEY"] = (
        mapping_df["raw_name"]
        .map(normalize_account_name)
    )

    mapping_df = mapping_df[
        mapping_df["ACCOUNT_DESCRIPTION_KEY"].ne("")
    ].copy()

    conflicts = (
        mapping_df
        .groupby("ACCOUNT_DESCRIPTION_KEY")["sub_bge_alias"]
        .nunique()
    )

    conflicting_keys = (
        conflicts[conflicts > 1]
        .index
        .tolist()
    )

    if conflicting_keys:
        conflicting_rows = (
            mapping_df[
                mapping_df["ACCOUNT_DESCRIPTION_KEY"].isin(
                    conflicting_keys
                )
            ][
                [
                    "raw_name",
                    "sub_bge_alias",
                    "ACCOUNT_DESCRIPTION_KEY",
                ]
            ]
            .sort_values(
                [
                    "ACCOUNT_DESCRIPTION_KEY",
                    "sub_bge_alias",
                ],
                kind="stable",
            )
        )

        raise ValueError(
            "Some Account Description names map to multiple aliases:\n\n"
            + conflicting_rows.to_string(index=False)
        )

    mapping_df = mapping_df.drop_duplicates(
        subset=["ACCOUNT_DESCRIPTION_KEY"],
        keep="last",
    )

    account_mapping = dict(
        zip(
            mapping_df["ACCOUNT_DESCRIPTION_KEY"],
            mapping_df["sub_bge_alias"],
        )
    )

    print(
        f"Loaded {len(account_mapping):,} Account Description mappings "
        f"from {ACCOUNT_MAPPING_FILE.name}"
    )

    return account_mapping


# -----------------------------------------------------------------------------
# LOAD TLS DESCRIPTIONS AND CATEGORIES FROM LTO LIST
# -----------------------------------------------------------------------------
def load_tls_master() -> pd.DataFrame:
    """
    Load TLS descriptions and categories directly from the LTO List.

    Required columns:
      - Charge Description
      - TLS Category

    The separate Limited Time Onboarded Services consolidated workbook is no
    longer required.
    """
    if not TLS_SOURCE_FILE.exists():
        raise FileNotFoundError(
            "TLS source file was not found:\n"
            f"  {TLS_SOURCE_FILE}"
        )

    print(
        f"Reading TLS descriptions and categories from "
        f"{TLS_SOURCE_FILE.name}, sheet '{TLS_SOURCE_SHEET}' ..."
    )

    with pd.ExcelFile(TLS_SOURCE_FILE) as xls:
        if TLS_SOURCE_SHEET not in xls.sheet_names:
            raise ValueError(
                f"The worksheet '{TLS_SOURCE_SHEET}' was not found in "
                f"{TLS_SOURCE_FILE.name}.\n"
                f"Worksheets found: {xls.sheet_names}"
            )

        df = pd.read_excel(
            xls,
            sheet_name=TLS_SOURCE_SHEET,
            dtype=object,
        )

    if df.empty:
        raise ValueError(
            f"The worksheet '{TLS_SOURCE_SHEET}' is empty."
        )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    description_column = find_column(
        df.columns,
        [
            "Charge Description",
            "Detail Description",
            "Service Description",
            "TLS Reference Description",
            "Description",
        ],
    )

    category_column = find_column(
        df.columns,
        [
            "TLS Category",
            "Category",
            "Service Category",
        ],
    )

    if description_column is None:
        raise ValueError(
            f"No TLS description column was found in "
            f"'{TLS_SOURCE_SHEET}'.\n"
            "Expected one of:\n"
            "  - Charge Description\n"
            "  - Detail Description\n"
            "  - Service Description\n"
            "  - TLS Reference Description\n\n"
            f"Columns found: {list(df.columns)}"
        )

    if category_column is None:
        raise ValueError(
            f"No TLS category column was found in "
            f"'{TLS_SOURCE_SHEET}'.\n"
            "Expected one of:\n"
            "  - TLS Category\n"
            "  - Category\n"
            "  - Service Category\n\n"
            f"Columns found: {list(df.columns)}"
        )

    tls_master = pd.DataFrame(
        {
            "TLS Reference Description": (
                df[description_column]
                .map(clean_value)
            ),
            "Category": (
                df[category_column]
                .map(clean_value)
            ),
        }
    )

    tls_master["TLS_KEY"] = (
        tls_master["TLS Reference Description"]
        .map(normalize_text)
    )

    tls_master = tls_master[
        tls_master["TLS_KEY"].ne("")
    ].copy()

    if tls_master.empty:
        raise ValueError(
            f"No usable TLS descriptions were found in "
            f"'{TLS_SOURCE_SHEET}'."
        )

    tls_master.loc[
        tls_master["Category"].eq(""),
        "Category",
    ] = "Unclassified - Review"

    # Check whether one normalized TLS description has multiple categories.
    category_counts = (
        tls_master
        .groupby("TLS_KEY")["Category"]
        .nunique()
    )

    conflicting_keys = (
        category_counts[category_counts > 1]
        .index
        .tolist()
    )

    if conflicting_keys:
        conflicting_rows = (
            tls_master[
                tls_master["TLS_KEY"].isin(
                    conflicting_keys
                )
            ][
                [
                    "TLS Reference Description",
                    "Category",
                    "TLS_KEY",
                ]
            ]
            .drop_duplicates()
            .sort_values(
                [
                    "TLS_KEY",
                    "Category",
                ],
                kind="stable",
            )
        )

        raise ValueError(
            "Some TLS descriptions in the LTO List have more than one "
            "category.\n"
            "Each normalized TLS description must have only one category.\n\n"
            + conflicting_rows.to_string(index=False)
        )

    tls_master = (
        tls_master
        .drop_duplicates(
            subset=["TLS_KEY"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # Keep the existing output column structure.
    tls_master["Category Reference Description"] = (
        tls_master["TLS Reference Description"]
    )

    tls_master["Category Match Type"] = "From LTO List"
    tls_master["Category Match Score"] = 100.0

    print(
        f"Loaded {len(tls_master):,} unique TLS descriptions "
        f"with categories from the LTO List"
    )

    category_summary = (
        tls_master["Category"]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("TLS descriptions by category:")

    for category, count in category_summary.items():
        print(
            f"  {category}: {count:,}"
        )

    return tls_master


# -----------------------------------------------------------------------------
# LOAD MONTHLY REPORTS
# -----------------------------------------------------------------------------
def load_reports(
    account_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    Read every usable worksheet from the configured monthly reports.
    """
    frames = []

    for report_month, file_path in REPORT_FILES.items():
        if not file_path.exists():
            raise FileNotFoundError(
                f"Monthly report was not found:\n  {file_path}"
            )

        print(f"Reading {file_path.name} ...")

        with pd.ExcelFile(file_path) as xls:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(
                    xls,
                    sheet_name=sheet_name,
                    dtype=object,
                )

                if df.empty:
                    print(
                        f"  Skipped sheet '{sheet_name}': sheet is empty"
                    )
                    continue

                detail_column = find_column(
                    df.columns,
                    REPORT_COLUMN_ALIASES[
                        "detail_description"
                    ],
                )

                if detail_column is None:
                    print(
                        f"  Skipped sheet '{sheet_name}': "
                        "no description column"
                    )
                    continue

                output = pd.DataFrame(
                    index=df.index
                )

                output["BGE"] = sheet_name
                output["Report Month"] = report_month
                output["Source File"] = file_path.name
                output["Source Sheet"] = sheet_name

                output_titles = {
                    "account_number": "Account Number",
                    "account_description": "Account Description",
                    "service_number": "Service Number",
                    "detail_description": (
                        "Report Detail Description"
                    ),
                    "amount": "Amount",
                    "service_address": "Service Address",
                    "organization": "Organization",
                    "statement_date": "Statement Date",
                }

                for target, aliases in REPORT_COLUMN_ALIASES.items():
                    source_column = find_column(
                        df.columns,
                        aliases,
                    )

                    output_title = output_titles[target]

                    if source_column is not None:
                        output[output_title] = df[source_column]
                    else:
                        output[output_title] = ""

                output["ACCOUNT_DESCRIPTION_KEY"] = (
                    output["Account Description"]
                    .map(normalize_account_name)
                )

                output["sub_bge/service designee"] = (
                    output["ACCOUNT_DESCRIPTION_KEY"]
                    .map(account_mapping)
                    .fillna("Unmapped")
                )

                output = output.drop(
                    columns=["ACCOUNT_DESCRIPTION_KEY"]
                )

                output["Report Detail Description"] = (
                    output["Report Detail Description"]
                    .map(clean_value)
                )

                output = output[
                    output["Report Detail Description"].ne("")
                ].copy()

                output["REPORT_KEY"] = (
                    output["Report Detail Description"]
                    .map(normalize_text)
                )

                

                output["Amount"] = pd.to_numeric(
                    output["Amount"],
                    errors="coerce",
                )

                print(
                    f"  Loaded {len(output):,} usable rows "
                    f"from '{sheet_name}'"
                )

                frames.append(output)

    if not frames:
        raise ValueError(
            "No usable rows were found in the monthly reports."
        )

    reports = pd.concat(
        frames,
        ignore_index=True,
    )

    return reports


# -----------------------------------------------------------------------------
# MATCH REPORT DESCRIPTIONS TO THE CATEGORIZED LTO LIST
# -----------------------------------------------------------------------------
def build_tls_match_map(
    report_keys: list[str],
    tls_master: pd.DataFrame,
) -> dict[str, dict]:
    """
    Match normalized report descriptions against the categorized LTO List.

    Category information is returned directly from the matched LTO row.
    """
    tls_records = (
        tls_master
        .set_index("TLS_KEY")
        [
            [
                "TLS Reference Description",
                "Category",
                "Category Reference Description",
                "Category Match Type",
                "Category Match Score",
            ]
        ]
        .to_dict(orient="index")
    )

    tls_keys = list(tls_records)

    if not tls_keys:
        raise ValueError(
            "The categorized LTO List does not contain any usable TLS keys."
        )

    result = {}

    for index, report_key in enumerate(
        report_keys,
        start=1,
    ):
        if report_key in tls_records:
            matched_record = tls_records[report_key]

            result[report_key] = {
                "TLS_KEY": report_key,
                "TLS Reference Description": matched_record[
                    "TLS Reference Description"
                ],
                "TLS Match Type": "Exact",
                "TLS Match Score": 100.0,
                "Category": matched_record[
                    "Category"
                ],
                "Category Reference Description": matched_record[
                    "Category Reference Description"
                ],
                "Category Match Type": matched_record[
                    "Category Match Type"
                ],
                "Category Match Score": matched_record[
                    "Category Match Score"
                ],
            }

        else:
            matched_key, score = best_match(
                report_key,
                tls_keys,
            )

            if (
                matched_key
                and score >= TLS_FUZZY_THRESHOLD
            ):
                matched_record = tls_records[matched_key]

                result[report_key] = {
                    "TLS_KEY": matched_key,
                    "TLS Reference Description": matched_record[
                        "TLS Reference Description"
                    ],
                    "TLS Match Type": "Fuzzy",
                    "TLS Match Score": round(score, 1),
                    "Category": matched_record[
                        "Category"
                    ],
                    "Category Reference Description": matched_record[
                        "Category Reference Description"
                    ],
                    "Category Match Type": matched_record[
                        "Category Match Type"
                    ],
                    "Category Match Score": matched_record[
                        "Category Match Score"
                    ],
                }

            else:
                result[report_key] = {
                    "TLS_KEY": "",
                    "TLS Reference Description": "",
                    "TLS Match Type": "Not TLS",
                    "TLS Match Score": round(score, 1),
                    "Category": "",
                    "Category Reference Description": "",
                    "Category Match Type": "",
                    "Category Match Score": 0.0,
                }

        if index % 500 == 0:
            print(
                f"  Matched {index:,} unique report descriptions"
            )

    return result


# -----------------------------------------------------------------------------
# AGGREGATE MATCHED RESULTS
# -----------------------------------------------------------------------------
def aggregate_results(
    matched_rows: pd.DataFrame,
    latest_month: str,
) -> pd.DataFrame:
    """
    Aggregate exact TLS billing rows into the final BGE detail structure.
    """
    matched_rows = matched_rows.copy()

    matched_rows["Total Amount (September)"] = (
        matched_rows["Amount"].where(
            matched_rows["Report Month"].eq("2026-09"),
            0,
        )
    )

    matched_rows["Current Status"] = (
        matched_rows["Report Month"]
        .eq(latest_month)
        .map(
            {
                True: f"Current - seen in {latest_month}",
                False: (
                    f"Historical - not seen in {latest_month}"
                ),
            }
        )
    )

    grouping_columns = [
        "BGE",
        "Category",
        "TLS Reference Description",
        "Report Detail Description",
        "Account Number",
        "Service Number",
    ]

    for column in grouping_columns:
        matched_rows[column] = (
            matched_rows[column]
            .map(clean_value)
        )

    grouped = (
        matched_rows
        .groupby(
            grouping_columns,
            dropna=False,
            as_index=False,
        )
        .agg(
            **{
                "Current Status": (
                    "Current Status",
                    lambda values: (
                        f"Current - seen in {latest_month}"
                        if any(
                            "Current" in clean_value(value)
                            for value in values
                        )
                        else (
                            f"Historical - not seen in "
                            f"{latest_month}"
                        )
                    ),
                ),
                "Months Observed": (
                    "Report Month",
                    joined_unique,
                ),
                "First Month Seen": (
                    "Report Month",
                    "min",
                ),
                "Latest Month Seen": (
                    "Report Month",
                    "max",
                ),
                "Billing Row Count": (
                    "Report Detail Description",
                    "size",
                ),
                "Total Amount (September)": (
                    "Total Amount (September)",
                    "sum",
                ),
                "Total Amount": (
                    "Amount",
                    lambda values: values.sum(
                        min_count=1
                    ),
                ),
                "Account Description": (
                    "Account Description",
                    first_nonblank,
                ),
                "sub_bge/service designee": (
                    "sub_bge/service designee",
                    first_nonblank,
                ),
                "Organization": (
                    "Organization",
                    first_nonblank,
                ),
                "Service Address": (
                    "Service Address",
                    first_nonblank,
                ),
                "TLS Match Type": (
                    "TLS Match Type",
                    first_nonblank,
                ),
                "TLS Match Score": (
                    "TLS Match Score",
                    "max",
                ),
                "Category Reference Description": (
                    "Category Reference Description",
                    first_nonblank,
                ),
                "Category Match Type": (
                    "Category Match Type",
                    first_nonblank,
                ),
                "Category Match Score": (
                    "Category Match Score",
                    "max",
                ),
            }
        )
    )

    column_order = [
        "BGE",
        "Category",
        "Current Status",
        "TLS Reference Description",
        "Report Detail Description",
        "Account Number",
        "Account Description",
        "sub_bge/service designee",
        "Service Number",
        "Organization",
        "Service Address",
        "Months Observed",
        "First Month Seen",
        "Latest Month Seen",
        "Billing Row Count",
        "Total Amount (September)",
        "Total Amount",
        "TLS Match Type",
        "TLS Match Score",
        "Category Reference Description",
        "Category Match Type",
        "Category Match Score",
    ]

    grouped = grouped[column_order]

    grouped = grouped.sort_values(
        [
            "BGE",
            "Category",
            "TLS Reference Description",
            "Service Number",
        ],
        kind="stable",
    )

    return grouped


# -----------------------------------------------------------------------------
# EXCEL OUTPUT
# -----------------------------------------------------------------------------
def write_output(
    detail: pd.DataFrame,
    latest_month: str,
) -> None:
    """
    Create the Summary sheet and one worksheet per BGE.
    """
    detail = detail[
        detail["TLS Match Type"].eq("Exact")
        & detail["TLS Match Score"].eq(100)
    ].copy()

    detail["BGE"] = (
        detail["BGE"]
        .fillna("UNKNOWN BGE")
        .astype(str)
        .str.strip()
    )

    detail.loc[
        detail["BGE"].eq(""),
        "BGE",
    ] = "UNKNOWN BGE"

    summary_columns = [
        "BGE",
        "Category",
        "Distinct TLS Descriptions",
        "Distinct Services",
        "Billing Rows",
        "Total Amount (September)",
        "Total Amount",
    ]

    if detail.empty:
        summary = pd.DataFrame(
            columns=summary_columns
        )

    else:
        summary = (
            detail
            .groupby(
                [
                    "BGE",
                    "Category",
                ],
                dropna=False,
            )
            .agg(
                **{
                    "Distinct TLS Descriptions": (
                        "TLS Reference Description",
                        "nunique",
                    ),
                    "Distinct Services": (
                        "Service Number",
                        lambda values: (
                            values
                            .replace("", pd.NA)
                            .dropna()
                            .nunique()
                        ),
                    ),
                    "Billing Rows": (
                        "Billing Row Count",
                        "sum",
                    ),
                    "Total Amount (September)": (
                        "Total Amount (September)",
                        "sum",
                    ),
                    "Total Amount": (
                        "Total Amount",
                        "sum",
                    ),
                }
            )
            .reset_index()
            .sort_values(
                [
                    "BGE",
                    "Category",
                ],
                kind="stable",
            )
        )

    used_sheet_names = {
        "summary",
    }

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="xlsxwriter",
        datetime_format="yyyy-mm-dd",
    ) as writer:
        workbook = writer.book

        title_format = workbook.add_format(
            {
                "bold": True,
                "font_size": 16,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "align": "left",
                "valign": "vcenter",
            }
        )

        note_format = workbook.add_format(
            {
                "font_color": "#666666",
                "italic": True,
            }
        )

        header_format = workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#4472C4",
                "border": 0,
                "text_wrap": True,
                "valign": "top",
            }
        )

        normal_format = workbook.add_format(
            {
                "font_color": "#000000",
            }
        )

        matched_format = workbook.add_format(
            {
                "font_color": "#008000",
            }
        )

        money_format = workbook.add_format(
            {
                "font_color": "#000000",
                "num_format": (
                    "$#,##0.00;$#,##0.00;-"
                ),
            }
        )

        integer_format = workbook.add_format(
            {
                "font_color": "#000000",
                "num_format": "#,##0",
            }
        )

        table_style = "Table Style Medium 2"

        def format_sheet(
            worksheet,
            dataframe: pd.DataFrame,
            startrow: int = 0,
            table_name: str | None = None,
        ) -> None:
            """
            Apply the standard output formatting to a worksheet.
            """
            worksheet.hide_gridlines(2)
            worksheet.freeze_panes(
                startrow + 1,
                2,
            )

            row_count, column_count = dataframe.shape

            if column_count == 0:
                return

            for column_index, column_name in enumerate(
                dataframe.columns
            ):
                sample_lengths = [
                    len(str(column_name))
                ]

                if not dataframe.empty:
                    sample_lengths.extend(
                        dataframe[column_name]
                        .head(500)
                        .fillna("")
                        .astype(str)
                        .str.len()
                        .tolist()
                    )

                width = min(
                    max(sample_lengths) + 2,
                    42,
                )

                column_format = normal_format

                if column_name in {
                    "TLS Reference Description",
                    "Category",
                    "Category Reference Description",
                }:
                    column_format = matched_format

                worksheet.set_column(
                    column_index,
                    column_index,
                    max(width, 11),
                    column_format,
                )

                if column_name.startswith(
                    "Total Amount"
                ):
                    worksheet.set_column(
                        column_index,
                        column_index,
                        20,
                        money_format,
                    )

                elif column_name in {
                    "Billing Row Count",
                    "Distinct Services",
                    "Distinct TLS Descriptions",
                    "Billing Rows",
                }:
                    worksheet.set_column(
                        column_index,
                        column_index,
                        15,
                        integer_format,
                    )

            if row_count > 0:
                safe_table_name = re.sub(
                    r"[^A-Za-z0-9_]",
                    "_",
                    table_name or "Table",
                )[:240]

                worksheet.add_table(
                    startrow,
                    0,
                    startrow + row_count,
                    column_count - 1,
                    {
                        "name": safe_table_name,
                        "style": table_style,
                        "columns": [
                            {
                                "header": str(column),
                                "header_format": header_format,
                            }
                            for column in dataframe.columns
                        ],
                    },
                )

        # ---------------------------------------------------------------------
        # Summary worksheet
        # ---------------------------------------------------------------------
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
            startrow=4,
        )

        summary_worksheet = writer.sheets[
            "Summary"
        ]

        summary_last_column = max(
            len(summary.columns) - 1,
            0,
        )

        summary_worksheet.merge_range(
            0,
            0,
            0,
            summary_last_column,
            "TELUS Time Limited Services by BGE",
            title_format,
        )

        summary_worksheet.write(
            "A2",
            (
                "TLS descriptions and categories are taken directly "
                "from the LTO List worksheet."
            ),
            note_format,
        )

        summary_worksheet.write(
            "A3",
            (
                "Only exact TLS matches with a TLS match score of "
                "100% are included."
            ),
            note_format,
        )

        summary_worksheet.write(
            "A4",
            (
                f"Current-service filter month: {latest_month}. "
                "The workbook contains one worksheet for each BGE "
                "with qualifying TLS records."
            ),
            note_format,
        )

        format_sheet(
            summary_worksheet,
            summary,
            startrow=4,
            table_name="TLS_Summary",
        )

        # ---------------------------------------------------------------------
        # One worksheet per BGE
        # ---------------------------------------------------------------------
        bge_names = (
            detail["BGE"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .sort_values(
                key=lambda values: values.str.upper()
            )
            .tolist()
        )

        for sheet_counter, bge in enumerate(
            bge_names,
            start=1,
        ):
            export_df = detail[
                detail["BGE"].eq(bge)
            ].copy()

            if export_df.empty:
                continue

            export_df = (
                export_df
                .sort_values(
                    [
                        "Category",
                        "TLS Reference Description",
                        "Service Number",
                    ],
                    kind="stable",
                )
                .reset_index(drop=True)
            )

            sheet_name = safe_sheet_name(
                bge,
                used_sheet_names,
            )

            export_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

            format_sheet(
                writer.sheets[sheet_name],
                export_df,
                table_name=f"TLS_BGE_{sheet_counter}",
            )

    print(f"Created: {OUTPUT_FILE}")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main() -> None:
    """
    Run the complete TLS identification and reporting process.
    """
    required_files = (
        list(REPORT_FILES.values())
        + [
            TLS_SOURCE_FILE,
            ACCOUNT_MAPPING_FILE,
        ]
    )

    missing_files = [
        str(file_path)
        for file_path in required_files
        if not file_path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Missing input file(s):\n  "
            + "\n  ".join(missing_files)
        )

    latest_month = max(
        REPORT_FILES
    )

    print("=" * 80)
    print("TELUS TLS REPORT")
    print("=" * 80)

    if RAPIDFUZZ_AVAILABLE:
        print("Matching library: RapidFuzz")
    else:
        print(
            "Matching library: difflib fallback. "
            "Install rapidfuzz for faster matching."
        )

    print(
        f"Latest configured report month: {latest_month}"
    )

    # TLS description and TLS category both come from the LTO List.
    tls_master = load_tls_master()

    # The account mapping remains unchanged and supplies the
    # sub_bge/service designee output field.
    account_mapping = (
        load_account_description_mapping()
    )

    reports = load_reports(
        account_mapping
    )

    unique_report_descriptions = (
        reports["REPORT_KEY"]
        .drop_duplicates()
        .tolist()
    )

    print(
        f"Unique report descriptions: "
        f"{len(unique_report_descriptions):,}"
    )

    tls_match_map = build_tls_match_map(
        unique_report_descriptions,
        tls_master,
    )

    tls_match_df = (
        pd.DataFrame.from_dict(
            tls_match_map,
            orient="index",
        )
        .reset_index(
            names="REPORT_KEY"
        )
    )

    reports = reports.merge(
        tls_match_df,
        on="REPORT_KEY",
        how="left",
    )

    exact_match_mask = (
        reports["TLS_KEY"]
        .fillna("")
        .ne("")
        & reports["TLS Match Type"].eq("Exact")
        & reports["TLS Match Score"].eq(100)
    )

    matched = reports[
        exact_match_mask
    ].copy()

    print(
        f"Exact matched billing rows: {len(matched):,}"
    )

    if matched.empty:
        print(
            "WARNING: No exact TLS matches with a score of 100 "
            "were found."
        )

        empty_detail = pd.DataFrame(
            columns=[
                "BGE",
                "Category",
                "Current Status",
                "TLS Reference Description",
                "Report Detail Description",
                "Account Number",
                "Account Description",
                "sub_bge/service designee",
                "Service Number",
                "Organization",
                "Service Address",
                "Months Observed",
                "First Month Seen",
                "Latest Month Seen",
                "Billing Row Count",
                "Total Amount (September)",
                "Total Amount",
                "TLS Match Type",
                "TLS Match Score",
                "Category Reference Description",
                "Category Match Type",
                "Category Match Score",
            ]
        )

        write_output(
            empty_detail,
            latest_month,
        )

        return

    detail = aggregate_results(
        matched,
        latest_month,
    )

    if ONLY_CURRENT_SERVICES:
        before_filter_count = len(detail)

        detail = detail[
            detail["Latest Month Seen"].eq(
                latest_month
            )
        ].copy()

        after_filter_count = len(detail)

        print(
            "Current-service filter: "
            f"{before_filter_count:,} to "
            f"{after_filter_count:,} records"
        )

    if detail.empty:
        print(
            "WARNING: No services remain after the "
            "current-service filter."
        )

    else:
        print(
            f"Final output records: {len(detail):,}"
        )

        print(
            f"Final BGE worksheets: "
            f"{detail['BGE'].nunique():,}"
        )

    write_output(
        detail,
        latest_month,
    )

    print("=" * 80)
    print("PROCESS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        raise