import os
import logging
import urllib.parse
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client("glue")

JOB_NAME = os.environ["GLUE_JOB_NAME"]      
BUCKET = os.environ["BUCKET"]
PROVIDER = os.environ.get("PROVIDER", "telus")
REPORT_TYPE = os.environ.get("REPORT_TYPE", "quantities_reports")
SOURCE_PREFIX_BASE = os.environ.get("SOURCE_PREFIX_BASE", "raw")
OUTPUT_PREFIX_BASE = os.environ.get("OUTPUT_PREFIX_BASE", "processed")

def lambda_handler(event, context):
    # S3 event can contain multiple records
    for record in event.get("Records", []):
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")

        if not bucket or not key:
            continue

        key = urllib.parse.unquote_plus(key)

        # guardrails: only trigger on your expected path and .xlsx
        expected_prefix = f"{SOURCE_PREFIX_BASE}/{PROVIDER}/{REPORT_TYPE}/"
        if bucket != BUCKET:
            logger.info(f"Skipping event: bucket mismatch bucket={bucket}")
            continue
        if not key.startswith(expected_prefix):
            logger.info(f"Skipping event: key not under expected prefix key={key}")
            continue
        if not key.lower().endswith(".xlsx"):
            logger.info(f"Skipping event: not an xlsx key={key}")
            continue

        logger.info(f"Starting Glue job for s3://{bucket}/{key}")

        response = glue.start_job_run(
            JobName=JOB_NAME,
            Arguments={
                "--BUCKET": BUCKET,
                "--PROVIDER": PROVIDER,
                "--REPORT_TYPE": REPORT_TYPE,
                "--S3_KEY": key,
                "--SOURCE_PREFIX_BASE": SOURCE_PREFIX_BASE,
                "--OUTPUT_PREFIX_BASE": OUTPUT_PREFIX_BASE,
            },
        )

        logger.info(f"Glue job started jobRunId={response.get('JobRunId')}")

    return {"statusCode": 200}
