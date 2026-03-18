import json
import os
import boto3

glue = boto3.client("glue")

MONTH_MAP = {
    "January": "01", "February": "02", "March": "03",
    "April": "04", "May": "05", "June": "06",
    "July": "07", "August": "08", "September": "09",
    "October": "10", "November": "11", "December": "12"
}

# These come from Lambda environment variables set by Terraform
ROGERS_GLUE_JOB = os.environ.get("ROGERS_GLUE_JOB", "rogers_spend_ingestion")
RAW_BUCKET_ENV  = os.environ["RAW_BUCKET"]
OUTPUT_BUCKET   = os.environ["OUTPUT_BUCKET"]


def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    for record in event.get("Records", []):
        if not record["eventName"].startswith("ObjectCreated"):
            continue

        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        # Expect key: raw/rogers/spend_reports/{YEAR}/{MonthName}/file.xlsx
        parts = key.split("/")
        if len(parts) < 6:
            print("Invalid key structure, skipping:", key)
            continue

        raw_flag, provider, report_type, year, month_name = parts[:5]
        filename = parts[-1]

        if raw_flag != "raw":
            print("Not under raw/, skipping:", key)
            continue

        if provider.lower() != "rogers":
            print("Skipping non-Rogers file:", key)
            continue

        if report_type != "spend_reports":
            print("Skipping non-spend report:", key)
            continue

        if not filename.lower().endswith(".xlsx"):
            print("Skipping non-xlsx:", key)
            continue

        month_num = MONTH_MAP.get(month_name)
        if not month_num:
            print("Invalid month:", month_name)
            continue

        glue_args = {
            "--RAW_BUCKET": RAW_BUCKET_ENV,
            "--OUTPUT_BUCKET": OUTPUT_BUCKET,
            "--YEAR": year,
            "--MONTH_NAME": month_name,
            "--MONTH_NUM": month_num,
        }

        print(f"Triggering Rogers Glue job {ROGERS_GLUE_JOB} with args {glue_args}")

        resp = glue.start_job_run(
            JobName=ROGERS_GLUE_JOB,
            Arguments=glue_args
        )

        print("Glue response:", resp)

    return {"statusCode": 200, "body": "OK"}
