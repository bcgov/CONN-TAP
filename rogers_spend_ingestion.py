import io
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
YEAR          = args["YEAR"]       # e.g. "2025"
MONTH_NAME    = args["MONTH_NAME"] # e.g. "June"
MONTH_NUM     = args["MONTH_NUM"]  # e.g. "06"

RAW_PREFIX    = f"raw/rogers/spend_reports/{YEAR}/{MONTH_NAME}/"
OUTPUT_PREFIX = f"processed/rogers/spend_reports/{YEAR}/{MONTH_NUM}/"

print("RAW_PREFIX:   ", RAW_PREFIX)
print("OUTPUT_PREFIX:", OUTPUT_PREFIX)

# Spark + Glue initialization
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init("rogers_spend_ingestion", args)

# boto3 for S3 file access
s3_client = boto3.client("s3")

# Find the Rogers spend Excel file
def find_rogers_spend_file(bucket: str, raw_prefix: str, year: str) -> str:
    """
    Look under raw_prefix for a Rogers Usage & Spend workbook:
      - contains the year in the filename (e.g. '2025')
      - contains 'administrator', 'usage', 'spend'
      - ends with .xlsx

    We do NOT check the month in the filename because the month
    is already encoded in the folder name.
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    candidates = []

    for page in paginator.paginate(Bucket=bucket, Prefix=raw_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.split("/")[-1].lower()

            if (
                year.lower() in filename
                and "administrator" in filename
                and "usage" in filename
                and "spend" in filename
                and filename.endswith(".xlsx")
            ):
                candidates.append(key)

    if not candidates:
        raise ValueError(
            f"No Rogers spend report found for {year} under s3://{bucket}/{raw_prefix}"
        )

    candidates.sort()
    return candidates[-1]


# Read + clean the Usage_&_Spend sheet (pandas)
def combine_rogers_spend_report(bucket: str, key: str, year: str, month_num: str) -> pd.DataFrame:
    """
    Download Rogers Excel from S3, clean the Usage_&_Spend sheet,
    and return a pandas DataFrame ready to be written as a single parquet file.
    """
    print(f"\nDownloading: s3://{bucket}/{key}\n")

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()

    sheet_name = "Usage_&_Spend"
    df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name)
    print(f"Loaded sheet '{sheet_name}' with shape: {df.shape}")

    if df.empty:
        raise ValueError(f"Sheet '{sheet_name}' is empty in workbook {key}")

    # Drop rows where all columns are NaN
    df = df.dropna(how="all")

    # Remove repeated header rows (row values equal to column names)
    if not df.empty:
        mask_header = df.apply(lambda row: list(row.values) == list(df.columns), axis=1)
        df = df[~mask_header]

    if df.empty:
        raise ValueError(
            f"Sheet '{sheet_name}' has no usable data after cleaning in workbook {key}"
        )

    print(f"Usable rows after cleaning: {df.shape[0]}")

    # Drop duplicate columns (same name repeated)
    df = df.loc[:, ~df.columns.duplicated()]

    # Add metadata / entity
    df["entity_name"] = "Rogers"
    df["ingestion_year"] = str(year)
    df["ingestion_month"] = str(month_num)
    df["ingestion_ts"] = datetime.utcnow()

    # Force everything to string (avoid type conflicts)
    df = df.applymap(lambda x: "" if pd.isna(x) else str(x))

    print(f"Final pandas shape: {df.shape}")
    return df

# Write a single parquet file
def write_parquet_single_file(pdf: pd.DataFrame,
                              bucket: str,
                              prefix: str,
                              year: str,
                              month_num: str):
    """
    Write ONE parquet file to S3 using pandas + BytesIO.
    """
    parquet_key = f"{prefix}combined_{year}_{month_num}_rogers_spend_report.parquet"
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
print(f"Processing Rogers Spend for {MONTH_NAME} {YEAR}")

rogers_key = find_rogers_spend_file(RAW_BUCKET, RAW_PREFIX, YEAR)
print("Found file:", rogers_key)

combined_pdf = combine_rogers_spend_report(RAW_BUCKET, rogers_key, YEAR, MONTH_NUM)
write_parquet_single_file(combined_pdf, OUTPUT_BUCKET, OUTPUT_PREFIX, YEAR, MONTH_NUM)

job.commit()

print("Rogers ETL Completed Successfully.")
