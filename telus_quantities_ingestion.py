import io
import re
import sys
import logging
from datetime import datetime

import boto3
import pandas as pd

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# args
ARG_KEYS = [
    "JOB_NAME",
    "BUCKET",
    "PROVIDER",
    "REPORT_TYPE",
    "S3_KEY",                 
    "YEAR",                   
    "MONTH_NAME",             
    "MONTH_NUM",              
    "SOURCE_PREFIX_BASE",     
    "OUTPUT_PREFIX_BASE",   
]

args = getResolvedOptions(sys.argv, [k for k in ARG_KEYS if f"--{k}" in " ".join(sys.argv)])

BUCKET = args["BUCKET"]
PROVIDER = args["PROVIDER"]
REPORT_TYPE = args["REPORT_TYPE"]

SOURCE_PREFIX_BASE = args.get("SOURCE_PREFIX_BASE", "raw")
OUTPUT_PREFIX_BASE = args.get("OUTPUT_PREFIX_BASE", "processed")

S3_KEY = args.get("S3_KEY")
YEAR = args.get("YEAR")
MONTH_NAME = args.get("MONTH_NAME")
MONTH_NUM = args.get("MONTH_NUM")

# Spark + Glue init
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

s3_client = boto3.client("s3")

# logic implementation
MONTHLY_SERVICES_RE = re.compile(r"^\s*\S+\s+MONTHLY\s+SERVICES\s*$", re.IGNORECASE)

# check that regex pattern is getting correct sheet
def is_monthly_services_sheet(sheet_name: str) -> bool:
    return bool(MONTHLY_SERVICES_RE.match(sheet_name or ""))

# extract entity name
def first_word_entity(sheet_name: str) -> str:
    return (sheet_name or "").strip().split()[0] if sheet_name else ""

# remove remove repeated header rows
def remove_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.dropna(how="all")
    if df.empty:
        return df

    cols = list(df.columns)

    def is_header_row(row):
        return list(row.values) == cols

    mask = df.apply(is_header_row, axis=1)
    return df.loc[~mask].copy()

# enforce unique columns
def make_unique_columns(cols):
    seen = {}
    out = []
    for c in cols:
        c = str(c)
        if c not in seen:
            seen[c] = 1
            out.append(c)
        else:
            seen[c] += 1
            out.append(f"{c}_{seen[c]}")
    return out

# rename columns - check this incase Telus changes this later on
def rename_tbd_columns_for_monthly_services(df: pd.DataFrame) -> pd.DataFrame:
    """
        Rename any 'TBD', 'TBD.1', 'TBD.2'... columns based on their values.
          - Lowercase values first
          - if column contains wireless/wireline + (data|voice) => column name = Source
          - if column contains SRVEQUIP or Monthly Local Services => column name = Source System
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    tbd_cols = [
        c for c in df.columns
        if re.fullmatch(r"tbd(\.\d+)?", str(c).strip().lower())
    ]

    rename_map = {}

    for col in tbd_cols:
        s = df[col].astype(str).str.strip().str.lower()
        s = s.replace({"nan": "", "none": ""})
        df[col] = s

        has_source = (
            s.str.contains(r"\bwire(?:less|line)\s+(data|voice)\b", regex=True, na=False).any()
        )
        has_source_system = (
            s.str.contains(r"\b(srvequip|monthly local services)\b", regex=True, na=False).any()
        )

        if has_source:
            rename_map[col] = "Source"
        elif has_source_system:
            rename_map[col] = "Source System"

    if rename_map:
        df = df.rename(columns=rename_map)

    df.columns = make_unique_columns(df.columns)
    return df


# check that the file exists in S3
def parse_year_month_from_key(key: str):
    """
    Expected layout:
      raw/{provider}/{report_type}/{year}/{month_name}/<file>.xlsx

    Returns: (year, month_name)
    """
    parts = key.split("/")
    # minimal validation
    if len(parts) < 6:
        raise ValueError(f"Unexpected key format: {key}")

    # parts: [raw, provider, report_type, year, month_name, filename]
    return parts[3], parts[4]

# check for the latest quantities file
def find_latest_quantities_file(bucket: str, raw_prefix: str, year: str, month_name: str) -> str:
    paginator = s3_client.get_paginator("list_objects_v2")
    candidates = []

    for page in paginator.paginate(Bucket=bucket, Prefix=raw_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.split("/")[-1].lower()

            if (
                month_name.lower() in filename
                and year in filename
                and "quantit" in filename
                and "consolidated" in filename
                and filename.endswith(".xlsx")
            ):
                candidates.append(key)

    if not candidates:
        raise ValueError(f"No Quantities report found under s3://{bucket}/{raw_prefix} for {month_name} {year}")

    candidates.sort()
    return candidates[-1]

# read file from S3
def read_xlsx_from_s3(bucket: str, key: str) -> dict:
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    return pd.read_excel(io.BytesIO(data), sheet_name=None)

# Main ETL logic
def run():
    global YEAR, MONTH_NAME, MONTH_NUM

    # determine time params
    if S3_KEY:
        YEAR, MONTH_NAME = parse_year_month_from_key(S3_KEY)
        if not MONTH_NUM:
            # derive from month name if not explicitly passed
            month_lookup = {
                "january":"01","february":"02","march":"03","april":"04","may":"05","june":"06",
                "july":"07","august":"08","september":"09","october":"10","november":"11","december":"12"
            }
            MONTH_NUM = month_lookup.get(MONTH_NAME.strip().lower())
            if not MONTH_NUM:
                raise ValueError(f"Could not derive MONTH_NUM from MONTH_NAME={MONTH_NAME}")
    else:
        # manual run requires YEAR, MONTH_NAME, MONTH_NUM
        if not (YEAR and MONTH_NAME and MONTH_NUM):
            raise ValueError("Provide either S3_KEY, or YEAR+MONTH_NAME+MONTH_NUM for manual run.")

    RAW_PREFIX = f"{SOURCE_PREFIX_BASE}/{PROVIDER}/{REPORT_TYPE}/{YEAR}/{MONTH_NAME}/"
    OUTPUT_PREFIX = f"{OUTPUT_PREFIX_BASE}/{PROVIDER}/{REPORT_TYPE}/{YEAR}/{MONTH_NUM}/"

    # choose file:
    # - If triggered with S3_KEY, prefer that exact object (it is the new file),
    #   but still validate it's an xlsx and matches expected naming.
    if S3_KEY:
        key = S3_KEY
    else:
        key = find_latest_quantities_file(BUCKET, RAW_PREFIX, YEAR, MONTH_NAME)

    logger.info(f"Processing quantities report. bucket={BUCKET}, key={key}")

    all_sheets = read_xlsx_from_s3(BUCKET, key)

    combined = []
    for sheet_name, df in all_sheets.items():
        if not is_monthly_services_sheet(sheet_name):
            continue
        if df is None or df.empty:
            continue

        df = remove_repeated_header_rows(df)
        if df is None or df.empty:
            continue

        df = rename_tbd_columns_for_monthly_services(df)

        df["entity"] = first_word_entity(sheet_name)
        df["sheet_name"] = sheet_name

        combined.append(df)

    if not combined:
        raise ValueError("No usable '<entity> MONTHLY SERVICES' sheets found in this Quantities report.")

    monthly_services_df = pd.concat(combined, ignore_index=True)
    monthly_services_df = monthly_services_df.loc[:, ~monthly_services_df.columns.duplicated()].copy()

    monthly_services_df["ingestion_year"] = YEAR
    monthly_services_df["ingestion_month"] = MONTH_NUM
    monthly_services_df["ingestion_ts"] = datetime.utcnow().isoformat()

    # make strings only (stable parquet)
    monthly_services_df = monthly_services_df.applymap(lambda x: "" if pd.isna(x) else str(x))

    parquet_key = f"{OUTPUT_PREFIX}combined_{YEAR}_{MONTH_NUM}_monthly_services.parquet"

    # pandas -> parquet -> upload
    buffer = io.BytesIO()
    monthly_services_df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    s3_client.put_object(
        Bucket=BUCKET,
        Key=parquet_key,
        Body=buffer.getvalue()
    )

    logger.info(f"Wrote parquet to s3://{BUCKET}/{parquet_key}")

run()