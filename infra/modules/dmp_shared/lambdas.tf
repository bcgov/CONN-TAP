resource "aws_lambda_function" "lambda_ngta_rogers" {
  function_name = "lambda-ngta-rogers"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  s3_bucket = var.glue_assets_bucket_name
  s3_key    = aws_s3_object.lambda_ngta_rogers_zip.key

  environment {
    variables = {
      OUTPUT_BUCKET   = var.ngta_raw_bucket_name
      RAW_BUCKET      = var.ngta_raw_bucket_name
      ROGERS_GLUE_JOB = "rogers_spend_ingestion"
    }
  }
}

resource "aws_lambda_function" "lambda_ngta_telus" {
  function_name = "lambda-ngta-telus"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  s3_bucket = var.glue_assets_bucket_name
  s3_key    = aws_s3_object.lambda_ngta_telus_zip.key

  environment {
    variables = {
      GLUE_JOB_NAME = "telus_spend_ingestion"
      OUTPUT_BUCKET = var.ngta_raw_bucket_name
      RAW_BUCKET    = var.ngta_raw_bucket_name
    }
  }
}

resource "aws_lambda_function" "lambda_ngta_telus_quantities" {
  function_name = "lambda-ngta-telus-quantities"
  role          = aws_iam_role.lambda_ngta_telus_quantities_role.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  s3_bucket = var.glue_assets_bucket_name
  s3_key    = aws_s3_object.lambda_ngta_telus_quantities_zip.key

  environment {
    variables = {
      BUCKET             = var.ngta_raw_bucket_name
      GLUE_JOB_NAME      = "telus_quantities_ingestion"
      OUTPUT_PREFIX_BASE = "processed"
      PROVIDER           = "telus"
      REPORT_TYPE        = "quantities_reports"
      SOURCE_PREFIX_BASE = "raw"
    }
  }
}

resource "aws_lambda_function" "lambda_tsma_fact" {
  function_name = "lambda-tsma-fact"
  role          = aws_iam_role.lambda_tsma_fact_role.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  s3_bucket = var.glue_assets_bucket_name
  s3_key    = aws_s3_object.lambda_tsma_fact_zip.key

  environment {
    variables = {
      GLUE_JOB_NAME = "tsma-fact"
    }
  }
}

resource "aws_lambda_function" "lambda_tsma_qsr" {
  function_name = "lambda-tsma-qsr"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  s3_bucket = var.glue_assets_bucket_name
  s3_key    = aws_s3_object.lambda_tsma_qsr_zip.key

  timeout = 30

  environment {
    variables = {
      GLUE_JOB_NAME = "tsma_qsr_ingestion"
      OUTPUT_BUCKET = var.tsma_raw_bucket_name
      RAW_BUCKET    = var.tsma_raw_bucket_name
    }
  }
}