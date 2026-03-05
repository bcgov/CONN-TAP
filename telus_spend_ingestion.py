import io
import re
import sys
import boto3
import pandas as pd
from datetime import datetime

from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Glue args
args = getResolvedOptions(sys.argv, [
    "RAW_BUCKET",
    "OUTPUT_BUCKET",
    "YEAR",
    "MONTH_NAME",
    "MONTH_NUM",
])

RAW_BUCKET    = args["RAW_BUCKET"]
OUTPUT_BUCKET = args["OUTPUT_BUCKET"]
YEAR          = args["YEAR"]
MONTH_NAME    = args["MONTH_NAME"]
MONTH_NUM     = args["MONTH_NUM"]

RAW_PREFIX    = f"raw/telus/spend_reports/{YEAR}/{MONTH_NAME}/"
OUTPUT_PREFIX = f"processed/telus/spend_reports/{YEAR}/{MONTH_NUM}/"

# Spark + Glue initialization (still fine even if we don't use Spark to write)
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# boto3 for S3 file access
s3_client = boto3.client("s3")


def find_telus_spend_file(bucket, raw_prefix, year, month_name):
    paginator = s3_client.get_paginator("list_objects_v2")
    candidates = []

    for page in paginator.paginate(Bucket=bucket, Prefix=raw_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.split("/")[-1].lower()

            if (
                month_name.lower() in filename
                and year.lower() in filename
                and "consolidated" in filename
                and "spend" in filename
                and filename.endswith(".xlsx")
            ):
                candidates.append(key)

    if not candidates:
        raise ValueError(f"Could not find Telus spend report for {month_name} {year}")

    candidates.sort()
    return candidates[-1]


def combine_spend_report(bucket, key, year, month_num):
    """
    Download Excel from S3, clean all sheets, combine, and return
    a **pandas** DataFrame (same as local notebook).
    """
    print(f"\nDownloading: s3://{bucket}/{key}\n")

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()

    # Read all sheets into pandas
    all_sheets = pd.read_excel(io.BytesIO(data), sheet_name=None)
    print(f"Found {len(all_sheets)} sheets in workbook")

    combined_sheets = []

    for sheet_name, df in all_sheets.items():
        print(f"\nInspecting sheet: {sheet_name}")

        if df.empty:
            print(f"Skipping empty sheet: {sheet_name}")
            continue

        # Drop rows where all columns are NaN
        df = df.dropna(how="all")

        # Drop rows that look like repeated headers (row equals column names)
        if not df.empty:
            mask_header_rows = df.apply(
                lambda row: list(row.values) == list(df.columns),
                axis=1
            )
            df = df[~mask_header_rows]

        # Ignore sheets that end up empty after cleaning
        if df.shape[0] == 0:
            print(f"Skipping sheet '{sheet_name}' — no usable data after cleaning.")
            continue

        print(f"Included sheet '{sheet_name}' with {df.shape[0]} rows, {df.shape[1]} cols")

        # Add metadata: entity = sheet name
        df["entity_name"] = sheet_name

        combined_sheets.append(df)

    if not combined_sheets:
        raise ValueError("No valid data found in any sheets of the workbook.")

    # Concatenate all cleaned sheets
    combined_pdf = pd.concat(combined_sheets, ignore_index=True)

    # Drop duplicate columns (same name repeated)
    combined_pdf = combined_pdf.loc[:, ~combined_pdf.columns.duplicated()]

    print(f"\nCombined DataFrame shape (pandas): {combined_pdf.shape}\n")

    # Add ingestion metadata
    combined_pdf["ingestion_year"] = str(year)
    combined_pdf["ingestion_month"] = str(month_num)
    combined_pdf["ingestion_ts"] = datetime.utcnow()

    # force all columns to string (same as notebook)
    combined_pdf = combined_pdf.applymap(lambda x: "" if pd.isna(x) else str(x))

    return combined_pdf


def write_parquet_single_file(pdf: pd.DataFrame, bucket: str, prefix: str,
                              year: str, month_num: str):
    """
    Write a **single** parquet file to S3 using pandas + BytesIO,
    same behaviour as the local notebook.
    """
    # Build S3 key for the parquet file
    parquet_key = f"{prefix}combined_{year}_{month_num}_spend_report.parquet"
    output_uri = f"s3://{bucket}/{parquet_key}"

    print("Writing parquet to:", output_uri)

    buffer = io.BytesIO()
    pdf.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    s3_client.put_object(
        Bucket=bucket,
        Key=parquet_key,
        Body=buffer.getvalue()
    )

    print("Written single parquet file:", output_uri)


# MAIN EXECUTION FLOW
print(f"Processing Telus Spend for {MONTH_NAME} {YEAR}")

job = Job(glueContext)
job.init("telus_spend_ingestion", args)

key = find_telus_spend_file(RAW_BUCKET, RAW_PREFIX, YEAR, MONTH_NAME)
print("Found file:", key)

combined_pdf = combine_spend_report(RAW_BUCKET, key, YEAR, MONTH_NUM)
write_parquet_single_file(combined_pdf, OUTPUT_BUCKET, OUTPUT_PREFIX, YEAR, MONTH_NUM)

job.commit()

print("ETL Completed Successfully.")