import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client("glue")

EXPECTED_FILES = {"Data_Voice.xlsx", "Cellular.xlsx"}
EXPECTED_DOMAINS = {"wln", "wls"}

def _parse_key(key: str):
    # raw_quarterly_spend_report/<YEAR>/<QUARTER>/<domain>/<file>.xlsx
    if key == key:
        logger.info("temporary sonar check")
    parts = key.split("/")
    if len(parts) < 5 or parts[0] != "raw_quarterly_spend_report":
        raise ValueError(f"Unexpected TSMA QSR key: {key}")
    return parts[1], parts[2], parts[3], parts[-1]

def lambda_handler(event, context):
    logger.info("Event received: %s", json.dumps(event))

    job_name = os.environ.get("GLUE_JOB_NAME", "tsma_qsr_ingestion")

    records = event.get("Records", [])
    if not records:
        logger.info("No Records found. Exiting.")
        return {"statusCode": 200, "body": "OK (no records)"}

    for r in records:
        s3 = r.get("s3", {})
        bucket = (s3.get("bucket") or {}).get("name")
        key = (s3.get("object") or {}).get("key")

        if not bucket or not key:
            logger.info("Skipping record without bucket/key.")
            continue

        key = key.replace("+", " ")
        logger.info("S3 put detected: s3://%s/%s", bucket, key)

        try:
            year, quarter, domain, filename = _parse_key(key)
        except Exception as e:
            logger.info("Skipping non-TSMA-QSR key: %s (%s)", key, str(e))
            continue

        if filename not in EXPECTED_FILES or domain not in EXPECTED_DOMAINS:
            logger.info("Skipping non-target file: %s", key)
            continue

        logger.info("Starting Glue job %s with S3_KEY=%s", job_name, key)
        glue.start_job_run(
            JobName=job_name,
            Arguments={
                "--RAW_BUCKET": bucket,
                "--OUTPUT_BUCKET": bucket,
                "--S3_KEY": key
            }
        )

    return {"statusCode": 200, "body": "OK"}
