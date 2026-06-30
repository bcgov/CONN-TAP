locals {
  ngta_ingest_dir = abspath("${var.repo_root}/lambda/ngta_ingest")
  build_dir       = abspath("${path.module}/.build")
  layer_zip       = "${local.build_dir}/ngta_ingest_layer.zip"
  function_zip    = "${local.build_dir}/lambda_ngta_ingest.zip"
}

# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

resource "aws_iam_role" "this" {
  name = "${var.name_prefix}-ngta-ingest-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "inline" {
  name = "${var.name_prefix}-ngta-ingest-s3"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = [
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/tsma/*",
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/tsma_lite/*",
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/tsma_other/*",
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/ngta/*",
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/pricebooks/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------------------------------------------------------------------------
# Dependency layer — built during plan/apply when zip is missing or stale
# ---------------------------------------------------------------------------

data "external" "layer_build" {
  program = ["python3", "${path.module}/build_layer.py"]

  query = {
    requirements_hash = filemd5("${local.ngta_ingest_dir}/requirements.txt")
    ingest_dir        = local.ngta_ingest_dir
    layer_zip         = local.layer_zip
  }
}

resource "aws_s3_object" "layer" {
  # The dependency layer exceeds Lambda's 50 MB direct-upload (filename) limit,
  # so it must be staged in S3 and referenced via s3_bucket/s3_key. The key uses
  # a prefix that does not match any aws_s3_bucket_notification filter below, so
  # uploading it never triggers the ingest Lambda.
  bucket = var.ngta_raw_bucket_name
  key    = "_lambda_artifacts/${var.name_prefix}-ngta-ingest-deps.zip"
  source = local.layer_zip
  etag   = filemd5(local.layer_zip)

  depends_on = [data.external.layer_build]
}

resource "aws_lambda_layer_version" "deps" {
  layer_name          = "${var.name_prefix}-ngta-ingest-deps"
  s3_bucket           = aws_s3_object.layer.bucket
  s3_key              = aws_s3_object.layer.key
  source_code_hash    = filebase64sha256(local.layer_zip)
  compatible_runtimes = ["python3.12"]

  depends_on = [aws_s3_object.layer]
}

# ---------------------------------------------------------------------------
# Function zip — handler + all three ingestion scripts
# ---------------------------------------------------------------------------

data "archive_file" "function" {
  type        = "zip"
  output_path = local.function_zip

  source {
    content  = file("${local.ngta_ingest_dir}/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/tsma_postgres_ingest/ingest_tsma_excel_folder.py")
    filename = "ingest_tsma_excel_folder.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py")
    filename = "ingest_raw_excel_folder.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py")
    filename = "ingest_tsma_other_excel_folder.py"
  }

  # Pricebook ingestion package — preserve the rogers/ and telus/ package layout
  # so the package's root-relative imports (common, rogers, telus) resolve.
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/common.py")
    filename = "common.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/__init__.py")
    filename = "rogers/__init__.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/ingest.py")
    filename = "rogers/ingest.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/parsers/__init__.py")
    filename = "rogers/parsers/__init__.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/parsers/cellular.py")
    filename = "rogers/parsers/cellular.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/parsers/data.py")
    filename = "rogers/parsers/data.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/parsers/professional_services.py")
    filename = "rogers/parsers/professional_services.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/rogers/parsers/voice.py")
    filename = "rogers/parsers/voice.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/telus/__init__.py")
    filename = "telus/__init__.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/telus/ingest.py")
    filename = "telus/ingest.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/telus/excel.py")
    filename = "telus/excel.py"
  }
  source {
    content  = file("${var.repo_root}/local_dev/raw_ingestion/ngta_pricebooks_ingest/telus/catalogues.py")
    filename = "telus/catalogues.py"
  }
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

resource "aws_security_group" "this" {
  name_prefix = "${var.name_prefix}-ngta-ingest-"
  description = "Outbound-only SG for the NGTA ingest Lambda."
  vpc_id      = var.vpc_id

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

resource "aws_vpc_security_group_ingress_rule" "rds_access" {
  security_group_id            = var.rds_security_group_id
  referenced_security_group_id = aws_security_group.this.id
  description                  = "PostgreSQL 5432 from ngta-ingest Lambda"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "this" {
  function_name    = "${var.name_prefix}-ngta-ingest"
  role             = aws_iam_role.this.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.function.output_path
  source_code_hash = data.archive_file.function.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]
  timeout          = 900
  memory_size      = 1024

  vpc_config {
    subnet_ids         = var.lambda_subnet_ids
    security_group_ids = [aws_security_group.this.id]
  }

  environment {
    variables = {
      DB_PASSWORD    = var.db_password
      DB_HOST        = var.rds_endpoint
      DB_NAME        = var.rds_db_name
      DRY_RUN        = tostring(var.dry_run)
      AWS_ACCOUNT_ID = var.account_id
    }
  }
}

# ---------------------------------------------------------------------------
# S3 trigger
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "allow_s3" {
  statement_id   = "AllowS3InvokeNGTAIngest"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.this.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket_name}"
  source_account = var.account_id
}

resource "aws_s3_bucket_notification" "triggers" {
  bucket = var.ngta_raw_bucket_name

  lambda_function {
    id                  = "tsma-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "tsma-lite-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma_lite/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "tsma-other-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma_other/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "ngta-telus-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "ngta/telus/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "ngta-rogers-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "ngta/rogers/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "pricebook-rogers-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "pricebooks/rogers/"
    filter_suffix       = ".pdf"
  }

  lambda_function {
    id                  = "pricebook-telus-ingest"
    lambda_function_arn = aws_lambda_function.this.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "pricebooks/telus/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [
    aws_lambda_function.this,
    aws_lambda_permission.allow_s3,
  ]

  # AWS removes S3 notifications when the target Lambda is deleted. The function
  # ARN is unchanged after recreate (same name), so Terraform would not detect
  # drift without forcing this resource to re-apply when the function changes.
  lifecycle {
    replace_triggered_by = [
      aws_lambda_function.this,
    ]
  }
}
