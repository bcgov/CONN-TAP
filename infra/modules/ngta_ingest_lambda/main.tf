locals {
  ngta_ingest_dir = "${var.repo_root}/lambda/ngta_ingest"
  layer_zip       = "${var.repo_root}/lambda/ngta_ingest/ngta_ingest_layer.zip"
  layer_build_dir = "${var.repo_root}/lambda/ngta_ingest/layer_build"
}

# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

resource "aws_iam_role" "this" {
  name = "lambda-ngta-ingest-role"

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
  name = "ngta-ingest-s3"
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
# Dependency layer — pip install runs locally during terraform apply
# Rebuilds only when requirements.txt changes
# ---------------------------------------------------------------------------

resource "null_resource" "layer_build" {
  triggers = {
    requirements = filemd5("${local.ngta_ingest_dir}/requirements.txt")
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      rm -rf "${local.layer_build_dir}"
      mkdir -p "${local.layer_build_dir}/python"
      pip install \
        --requirement "${local.ngta_ingest_dir}/requirements.txt" \
        --target "${local.layer_build_dir}/python" \
        --no-cache-dir \
        --quiet
      cd "${local.layer_build_dir}" && zip -r "${local.layer_zip}" python/ --quiet
      rm -rf "${local.layer_build_dir}"
    EOT
  }
}

resource "aws_lambda_layer_version" "deps" {
  layer_name          = "ngta-ingest-deps"
  filename            = local.layer_zip
  compatible_runtimes = ["python3.12"]
  depends_on          = [null_resource.layer_build]
}

# ---------------------------------------------------------------------------
# Function zip — handler + all three ingestion scripts
# ---------------------------------------------------------------------------

data "archive_file" "function" {
  type        = "zip"
  output_path = "${local.ngta_ingest_dir}/lambda_ngta_ingest.zip"

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
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

resource "aws_security_group" "this" {
  name_prefix = "lambda-ngta-ingest-"
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
  function_name    = "lambda-ngta-ingest"
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

  depends_on = [aws_lambda_permission.allow_s3]
}
