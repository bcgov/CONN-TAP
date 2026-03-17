import json
import os
import logging
import urllib.parse
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client("glue")

MONTH_MAP = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

GLUE_JOB_NAME = os.environ.get("GLUE_JOB_NAME")
if not GLUE_JOB_NAME:
    raise RuntimeError("GLUE_JOB_NAME environment variable is required")

RAW_BUCKET_ENV = os.environ.get("RAW_BUCKET")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")
  


def extract_params_from_key(key: str):
    """
    Expected S3 key pattern:
      raw/telus/spend_reports/<YEAR>/<MONTH_NAME>/<filename>.xlsx

    Example:
      raw/telus/spend_reports/2025/December/December 2025 Consolidated Spend Report.xlsx
    """
    parts = key.split("/")

    # Basic validation of the structure
    if len(parts) < 6:
        raise ValueError(f"Unexpected key structure: {key}")

    # parts: ["raw", "telus", "spend_reports", "2025", "December", "December 2025 ..."]
    year = parts[3]
    month_name = parts[4]

    month_num = MONTH_MAP.get(month_name.lower())
    if not month_num:
        raise ValueError(f"Could not map month name to number from key: {key}")

    return year, month_name, month_num


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    # S3 put event may contain multiple records, process first for now
    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    key = urllib.parse.unquote_plus(key)
    logger.info("Triggered by object: s3://%s/%s", bucket, key)

    # Optional: ignore non Telus spend paths or non Excel files
    if not key.lower().endswith(".xlsx"):
        logger.info("Object is not an .xlsx file. Skipping.")
        return {"statusCode": 200, "body": "Not an Excel file, skipped."}

    if "raw/telus/spend_reports/" not in key:
        logger.info("Object is not a Telus spend report path. Skipping.")
        return {"statusCode": 200, "body": "Not a Telus spend report, skipped."}

    # Optional sanity check on bucket if you want to restrict
    if RAW_BUCKET_ENV and bucket != RAW_BUCKET_ENV:
        logger.info("Bucket %s does not match configured RAW_BUCKET %s. Skipping.", bucket, RAW_BUCKET_ENV)
        return {"statusCode": 200, "body": "Unexpected bucket, skipped."}

    # Extract year and month values from key
    try:
        year, month_name, month_num = extract_params_from_key(key)
    except ValueError as e:
        logger.error("Failed to extract params from key: %s", e)
        raise

    logger.info("Derived parameters - YEAR: %s, MONTH_NAME: %s, MONTH_NUM: %s", year, month_name, month_num)

    # Build Glue job arguments
    glue_args = {
        "--RAW_BUCKET": bucket,
        "--OUTPUT_BUCKET": OUTPUT_BUCKET or bucket,
        "--YEAR": year,
        "--MONTH_NAME": month_name,
        "--MONTH_NUM": month_num,
    }

    logger.info("Starting Glue job %s with arguments: %s", GLUE_JOB_NAME, glue_args)

    response = glue.start_job_run(
        JobName=GLUE_JOB_NAME,
        Arguments=glue_args,
    )

    job_run_id = response["JobRunId"]
    logger.info("Started Glue job run: %s", job_run_id)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Glue job started", "jobRunId": job_run_id}),
    }