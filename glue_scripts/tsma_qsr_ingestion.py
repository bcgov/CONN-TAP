import io
import sys
import logging
from datetime import datetime

import boto3
import pandas as pd

from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
h = logging.StreamHandler(sys.stdout)
h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not logger.handlers:
    logger.addHandler(h)


# Args
req = getResolvedOptions(sys.argv, ["RAW_BUCKET", "OUTPUT_BUCKET"])
RAW_BUCKET = req["RAW_BUCKET"]
OUTPUT_BUCKET = req["OUTPUT_BUCKET"]

opt = {}
for k in ["S3_KEY", "YEAR", "QUARTER", "DOMAIN", "FILE"]:
    if f"--{k}" in sys.argv:
        opt.update(getResolvedOptions(sys.argv, [k]))

S3_KEY = opt.get("S3_KEY")
YEAR = opt.get("YEAR")
QUARTER = opt.get("QUARTER")
DOMAIN = opt.get("DOMAIN")
FILE = opt.get("FILE")


# Spark + Glue init
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init("tsma_qsr_ingestion", {**req, **opt})

s3 = boto3.client("s3")

EXPECTED_FILES = {"Data_Voice.xlsx", "Cellular.xlsx"}
EXPECTED_DOMAINS = {"wln", "wls"}


# Helpers
def parse_key(key: str):
    # raw_quarterly_spend_report/<YEAR>/<QUARTER>/<domain>/<file>.xlsx
    p = key.split("/")
    if len(p) < 5 or p[0] != "raw_quarterly_spend_report":
        raise ValueError(f"Unexpected TSMA QSR key: {key}")
    return p[1], p[2], p[3], p[-1]

def read_excel(bucket: str, key: str) -> pd.DataFrame:
    logger.info(f"Reading: s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    df = pd.read_excel(io.BytesIO(data), sheet_name=0)
    if df.empty:
        raise ValueError(f"Excel is empty: s3://{bucket}/{key}")
    return df

def write_single_parquet(pdf: pd.DataFrame, bucket: str, out_key: str):
    pdf = pdf.applymap(lambda x: "" if pd.isna(x) else str(x))
    buf = io.BytesIO()
    pdf.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    s3.put_object(Bucket=bucket, Key=out_key, Body=buf.getvalue())
    logger.info(f"Wrote: s3://{bucket}/{out_key}")

def ingest_one(year: str, quarter: str, domain: str, filename: str):
    raw_key = f"raw_quarterly_spend_report/{year}/{quarter}/{domain}/{filename}"
    df = read_excel(RAW_BUCKET, raw_key)

    df["ingestion_year"] = str(year)
    df["ingestion_quarter"] = str(quarter)
    df["domain"] = str(domain)
    df["ingestion_ts"] = datetime.utcnow().isoformat()

    out_file = filename.replace(".xlsx", ".parquet")
    out_key = f"processed_quarterly_spend_report/{year}/{quarter}/{domain}/{out_file}"
    write_single_parquet(df, OUTPUT_BUCKET, out_key)


# MAIN
try:
    logger.info("Starting TSMA QSR ingestion")

    if S3_KEY:
        y, q, d, f = parse_key(S3_KEY)
        if f not in EXPECTED_FILES or d not in EXPECTED_DOMAINS:
            logger.info(f"Skipping non-target file: {S3_KEY}")
        else:
            logger.info(f"Event run: year={y}, quarter={q}, domain={d}, file={f}")
            ingest_one(y, q, d, f)

    else:
        if not YEAR or not QUARTER:
            raise ValueError("Manual run requires --YEAR and --QUARTER when --S3_KEY is not provided.")

        if DOMAIN and FILE:
            if FILE not in EXPECTED_FILES or DOMAIN not in EXPECTED_DOMAINS:
                raise ValueError(f"Manual single-file must use domain in {EXPECTED_DOMAINS} and file in {EXPECTED_FILES}.")
            logger.info(f"Manual single: year={YEAR}, quarter={QUARTER}, domain={DOMAIN}, file={FILE}")
            ingest_one(YEAR, QUARTER, DOMAIN, FILE)
        else:
            logger.info(f"Manual full: year={YEAR}, quarter={QUARTER} (both files)")
            ingest_one(YEAR, QUARTER, "wln", "Data_Voice.xlsx")
            ingest_one(YEAR, QUARTER, "wls", "Cellular.xlsx")

    job.commit()
    logger.info("TSMA QSR ingestion completed successfully")

except Exception:
    logger.exception("TSMA QSR ingestion failed")
    raise