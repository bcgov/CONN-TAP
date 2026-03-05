import os, json, boto3

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME")
    if not job_name:
        return {"statusCode": 500, "body": "Missing GLUE_JOB_NAME env var"}
    glue.start_job_run(JobName=job_name)
    return {"statusCode": 200, "body": "OK"}
