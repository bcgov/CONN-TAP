import os
import boto3

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME", "tsma-fact")
    glue.start_job_run(JobName=job_name)
    return {"statusCode": 200, "body": "OK"}
