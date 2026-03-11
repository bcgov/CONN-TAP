############################################
# Build Lambda ZIPs locally (Terraform) and upload to Glue assets S3
############################################

data "archive_file" "lambda_ngta_rogers_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-ngta-rogers.zip"

  source {
    filename = "lambda_function.py"
    content  = <<PY
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _extract_s3_key(event):
    try:
        return event.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key")
    except Exception:
        return None

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("ROGERS_GLUE_JOB", "rogers_spend_ingestion")

    s3_key = _extract_s3_key(event)
    args = {}
    if s3_key:
        args["--S3_KEY"] = s3_key

    logger.info("Starting Glue job %s with args=%s", job_name, json.dumps(args))
    resp = glue.start_job_run(JobName=job_name, Arguments=args) if args else glue.start_job_run(JobName=job_name)

    return {"statusCode": 200, "body": json.dumps({"job": job_name, "run_id": resp.get("JobRunId")})}
PY
  }
}

data "archive_file" "lambda_ngta_telus_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-ngta-telus.zip"

  source {
    filename = "lambda_function.py"
    content  = <<PY
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _extract_s3_key(event):
    try:
        return event.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key")
    except Exception:
        return None

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME", "telus_spend_ingestion")

    s3_key = _extract_s3_key(event)
    args = {}
    if s3_key:
        args["--S3_KEY"] = s3_key

    logger.info("Starting Glue job %s with args=%s", job_name, json.dumps(args))
    resp = glue.start_job_run(JobName=job_name, Arguments=args) if args else glue.start_job_run(JobName=job_name)

    return {"statusCode": 200, "body": json.dumps({"job": job_name, "run_id": resp.get("JobRunId")})}
PY
  }
}

data "archive_file" "lambda_ngta_telus_quantities_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-ngta-telus-quantities.zip"

  source {
    filename = "lambda_function.py"
    content  = <<PY
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _extract_s3_key(event):
    try:
        return event.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key")
    except Exception:
        return None

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME", "telus_quantities_ingestion")

    s3_key = _extract_s3_key(event)
    args = {}
    if s3_key:
        args["--S3_KEY"] = s3_key

    logger.info("Starting Glue job %s with args=%s", job_name, json.dumps(args))
    resp = glue.start_job_run(JobName=job_name, Arguments=args) if args else glue.start_job_run(JobName=job_name)

    return {"statusCode": 200, "body": json.dumps({"job": job_name, "run_id": resp.get("JobRunId")})}
PY
  }
}

data "archive_file" "lambda_tsma_fact_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-tsma-fact.zip"

  source {
    filename = "lambda_function.py"
    content  = <<PY
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME", "tsma-fact")

    logger.info("Starting Glue job %s", job_name)
    resp = glue.start_job_run(JobName=job_name)

    return {"statusCode": 200, "body": json.dumps({"job": job_name, "run_id": resp.get("JobRunId")})}
PY
  }
}

data "archive_file" "lambda_tsma_qsr_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-tsma-qsr.zip"

  source {
    filename = "lambda_function.py"
    content  = <<PY
import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _extract_s3_key(event):
    try:
        return event.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key")
    except Exception:
        return None

def lambda_handler(event, context):
    glue = boto3.client("glue")
    job_name = os.environ.get("GLUE_JOB_NAME", "tsma_qsr_ingestion")

    s3_key = _extract_s3_key(event)
    args = {}
    if s3_key:
        args["--S3_KEY"] = s3_key

    logger.info("Starting Glue job %s with args=%s", job_name, json.dumps(args))
    resp = glue.start_job_run(JobName=job_name, Arguments=args) if args else glue.start_job_run(JobName=job_name)

    return {"statusCode": 200, "body": json.dumps({"job": job_name, "run_id": resp.get("JobRunId")})}
PY
  }
}

# Upload ZIPs to Glue assets bucket
resource "aws_s3_object" "lambda_ngta_rogers_zip" {
  bucket = aws_s3_bucket.glue_assets.bucket
  key    = "lambda/lambda-ngta-rogers.zip"
  source = data.archive_file.lambda_ngta_rogers_zip.output_path
  etag   = filemd5(data.archive_file.lambda_ngta_rogers_zip.output_path)
}

resource "aws_s3_object" "lambda_ngta_telus_zip" {
  bucket = aws_s3_bucket.glue_assets.bucket
  key    = "lambda/lambda-ngta-telus.zip"
  source = data.archive_file.lambda_ngta_telus_zip.output_path
  etag   = filemd5(data.archive_file.lambda_ngta_telus_zip.output_path)
}

resource "aws_s3_object" "lambda_ngta_telus_quantities_zip" {
  bucket = aws_s3_bucket.glue_assets.bucket
  key    = "lambda/lambda-ngta-telus-quantities.zip"
  source = data.archive_file.lambda_ngta_telus_quantities_zip.output_path
  etag   = filemd5(data.archive_file.lambda_ngta_telus_quantities_zip.output_path)
}

resource "aws_s3_object" "lambda_tsma_fact_zip" {
  bucket = aws_s3_bucket.glue_assets.bucket
  key    = "lambda/lambda-tsma-fact.zip"
  source = data.archive_file.lambda_tsma_fact_zip.output_path
  etag   = filemd5(data.archive_file.lambda_tsma_fact_zip.output_path)
}

resource "aws_s3_object" "lambda_tsma_qsr_zip" {
  bucket = aws_s3_bucket.glue_assets.bucket
  key    = "lambda/lambda-tsma-qsr.zip"
  source = data.archive_file.lambda_tsma_qsr_zip.output_path
  etag   = filemd5(data.archive_file.lambda_tsma_qsr_zip.output_path)
}

# Lambdas (created from the uploaded S3 objects)
resource "aws_lambda_function" "lambda_ngta_rogers" {
  function_name = "lambda-ngta-rogers"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket        = aws_s3_bucket.glue_assets.bucket
  s3_key           = aws_s3_object.lambda_ngta_rogers_zip.key
  source_code_hash = data.archive_file.lambda_ngta_rogers_zip.output_base64sha256

  environment {
    variables = {
      ROGERS_GLUE_JOB = "rogers_spend_ingestion"
      RAW_BUCKET      = var.ngta_raw_bucket
      OUTPUT_BUCKET   = var.ngta_raw_bucket
    }
  }

  depends_on = [aws_s3_object.lambda_ngta_rogers_zip]
}

resource "aws_lambda_function" "lambda_ngta_telus" {
  function_name = "lambda-ngta-telus"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket        = aws_s3_bucket.glue_assets.bucket
  s3_key           = aws_s3_object.lambda_ngta_telus_zip.key
  source_code_hash = data.archive_file.lambda_ngta_telus_zip.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME = "telus_spend_ingestion"
      RAW_BUCKET    = var.ngta_raw_bucket
      OUTPUT_BUCKET = var.ngta_raw_bucket
    }
  }

  depends_on = [aws_s3_object.lambda_ngta_telus_zip]
}

resource "aws_lambda_function" "lambda_ngta_telus_quantities" {
  function_name = "lambda-ngta-telus-quantities"
  role          = aws_iam_role.lambda_ngta_telus_quantities_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket        = aws_s3_bucket.glue_assets.bucket
  s3_key           = aws_s3_object.lambda_ngta_telus_quantities_zip.key
  source_code_hash = data.archive_file.lambda_ngta_telus_quantities_zip.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME      = "telus_quantities_ingestion"
      BUCKET             = var.ngta_raw_bucket
      SOURCE_PREFIX_BASE = "raw"
      OUTPUT_PREFIX_BASE = "processed"
      PROVIDER           = "telus"
      REPORT_TYPE        = "quantities_reports"
    }
  }

  depends_on = [aws_s3_object.lambda_ngta_telus_quantities_zip]
}

resource "aws_lambda_function" "lambda_tsma_fact" {
  function_name = "lambda-tsma-fact"
  role          = aws_iam_role.lambda_tsma_fact_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket        = aws_s3_bucket.glue_assets.bucket
  s3_key           = aws_s3_object.lambda_tsma_fact_zip.key
  source_code_hash = data.archive_file.lambda_tsma_fact_zip.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME = "tsma-fact"
    }
  }

  depends_on = [aws_s3_object.lambda_tsma_fact_zip]
}

resource "aws_lambda_function" "lambda_tsma_qsr" {
  function_name = "lambda-tsma-qsr"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  timeout     = 30
  memory_size = 128

  s3_bucket        = aws_s3_bucket.glue_assets.bucket
  s3_key           = aws_s3_object.lambda_tsma_qsr_zip.key
  source_code_hash = data.archive_file.lambda_tsma_qsr_zip.output_base64sha256

  environment {
    variables = {
      GLUE_JOB_NAME = "tsma_qsr_ingestion"
      RAW_BUCKET    = var.tsma_raw_bucket
      OUTPUT_BUCKET = var.tsma_raw_bucket
    }
  }

  depends_on = [aws_s3_object.lambda_tsma_qsr_zip]
}

# Permissions for S3 -> Lambda invoke
resource "aws_lambda_permission" "allow_s3_invoke_rogers" {
  statement_id   = "${var.account_id}_event_permissions_from_${var.ngta_raw_bucket}_for_lambda-ngta-rogers"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_rogers.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_telus" {
  statement_id   = "${var.account_id}_event_permissions_from_${var.ngta_raw_bucket}_for_lambda-ngta-telus"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_telus.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_telus_quantities" {
  statement_id   = "lambda-${var.account_id}-event_permissions-${var.ngta_raw_bucket}-for-lambda-ngta-telus-quantities"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_telus_quantities.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_tsma_qsr" {
  statement_id   = "AllowS3InvokeTSMAQSR"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_tsma_qsr.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.tsma_raw_bucket}"
  source_account = var.account_id
}