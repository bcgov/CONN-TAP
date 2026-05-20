locals {
  repo_root       = "${path.root}/../../.."
  ngta_ingest_dir = "${local.repo_root}/lambda/ngta_ingest"
  layer_zip       = "${local.repo_root}/lambda/ngta_ingest/ngta_ingest_layer.zip"
  layer_build_dir = "${local.repo_root}/lambda/ngta_ingest/layer_build"
}

# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

resource "aws_iam_role" "lambda_ngta_ingest" {
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

resource "aws_iam_role_policy" "lambda_ngta_ingest_inline" {
  name = "ngta-ingest-s3"
  role = aws_iam_role.lambda_ngta_ingest.id

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

resource "aws_iam_role_policy_attachment" "lambda_ngta_ingest_basic" {
  role       = aws_iam_role.lambda_ngta_ingest.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------------------------------------------------------------------------
# Dependency layer — pip install runs locally during terraform apply
# Rebuilds only when requirements.txt changes
# ---------------------------------------------------------------------------

resource "null_resource" "ngta_ingest_layer_build" {
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

resource "aws_lambda_layer_version" "ngta_ingest_deps" {
  layer_name          = "ngta-ingest-deps"
  filename            = local.layer_zip
  compatible_runtimes = ["python3.12"]
  source_code_hash    = try(filebase64sha256(local.layer_zip), "")
  depends_on          = [null_resource.ngta_ingest_layer_build]
}

# ---------------------------------------------------------------------------
# Function zip — handler + all three ingestion scripts
# ---------------------------------------------------------------------------

data "archive_file" "lambda_ngta_ingest" {
  type        = "zip"
  output_path = "${local.ngta_ingest_dir}/lambda_ngta_ingest.zip"

  source {
    content  = file("${local.ngta_ingest_dir}/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${local.repo_root}/local_dev/raw_ingestion/tsma_postgres_ingest/ingest_tsma_excel_folder.py")
    filename = "ingest_tsma_excel_folder.py"
  }
  source {
    content  = file("${local.repo_root}/local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py")
    filename = "ingest_raw_excel_folder.py"
  }
  source {
    content  = file("${local.repo_root}/local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py")
    filename = "ingest_tsma_other_excel_folder.py"
  }
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

resource "aws_security_group" "lambda_ngta_ingest" {
  name_prefix = "lambda-ngta-ingest-"
  description = "Outbound-only SG for the NGTA ingest Lambda."
  vpc_id      = data.aws_vpc.workload.id

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
  security_group_id            = module.platform_rds.security_group_id
  referenced_security_group_id = aws_security_group.lambda_ngta_ingest.id
  description                  = "PostgreSQL 5432 from ngta-ingest Lambda"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "lambda_ngta_ingest" {
  function_name    = "lambda-ngta-ingest"
  role             = aws_iam_role.lambda_ngta_ingest.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.lambda_ngta_ingest.output_path
  source_code_hash = data.archive_file.lambda_ngta_ingest.output_base64sha256
  layers           = [aws_lambda_layer_version.ngta_ingest_deps.arn]
  timeout          = 900
  memory_size      = 1024

  vpc_config {
    subnet_ids         = [data.aws_subnet.data_a.id, data.aws_subnet.data_b.id]
    security_group_ids = [aws_security_group.lambda_ngta_ingest.id]
  }

  environment {
    variables = {
      DB_PASSWORD = module.platform_rds.db_password
      DB_HOST     = module.platform_rds.db_instance_address
      DB_NAME     = module.platform_rds.db_name
      DRY_RUN     = "false"
    }
  }
}

# ---------------------------------------------------------------------------
# S3 trigger
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "allow_s3_invoke_ngta_ingest" {
  statement_id   = "AllowS3InvokeNGTAIngest"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_ingest.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket_name}"
  source_account = data.aws_caller_identity.current.account_id
}

resource "aws_s3_bucket_notification" "ngta_ingest_triggers" {
  bucket = var.ngta_raw_bucket_name

  lambda_function {
    id                  = "tsma-ingest"
    lambda_function_arn = aws_lambda_function.lambda_ngta_ingest.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "tsma-lite-ingest"
    lambda_function_arn = aws_lambda_function.lambda_ngta_ingest.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma_lite/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "tsma-other-ingest"
    lambda_function_arn = aws_lambda_function.lambda_ngta_ingest.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "tsma_other/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "ngta-telus-ingest"
    lambda_function_arn = aws_lambda_function.lambda_ngta_ingest.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "ngta/telus/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "ngta-rogers-ingest"
    lambda_function_arn = aws_lambda_function.lambda_ngta_ingest.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "ngta/rogers/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke_ngta_ingest]
}
