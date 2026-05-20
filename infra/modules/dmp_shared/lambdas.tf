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

resource "aws_lambda_layer_version" "ngta_ingest_deps" {
  layer_name          = "tsma-ingest-deps"
  s3_bucket           = var.glue_assets_bucket_name
  s3_key              = aws_s3_object.ngta_ingest_layer_zip.key
  compatible_runtimes = ["python3.12"]
  source_code_hash    = try(filebase64sha256("${var.assets_dir}/lambda/ngta_ingest/ngta_ingest_layer.zip"), "")
  depends_on          = [aws_s3_object.ngta_ingest_layer_zip]
}

resource "aws_security_group" "lambda_ngta_ingest" {
  name_prefix = "lambda-ngta-ingest-"
  description = "Outbound-only SG for the TSMA ingest Lambda (egress to RDS + internet for S3/SecretsManager)."
  vpc_id      = data.aws_vpc.selected.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_lambda_ngta_ingest" {
  count = var.rds_security_group_id != "" ? 1 : 0

  security_group_id            = var.rds_security_group_id
  referenced_security_group_id = aws_security_group.lambda_ngta_ingest.id
  description                  = "PostgreSQL 5432 from tsma-ingest Lambda"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_lambda_function" "lambda_ngta_ingest" {
  function_name    = "lambda-ngta-ingest"
  role             = aws_iam_role.lambda_ngta_ingest_role.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  s3_bucket        = var.glue_assets_bucket_name
  s3_key           = aws_s3_object.lambda_ngta_ingest_zip.key
  source_code_hash = data.archive_file.lambda_ngta_ingest.output_base64sha256
  layers           = [aws_lambda_layer_version.ngta_ingest_deps.arn]
  timeout          = 900
  memory_size      = 1024

  vpc_config {
    subnet_ids         = var.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda_ngta_ingest.id]
  }

  environment {
    variables = {
      DB_SECRET_ARN = var.rds_secret_arn
      DB_HOST       = var.rds_endpoint
      DB_NAME       = var.rds_db_name
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
