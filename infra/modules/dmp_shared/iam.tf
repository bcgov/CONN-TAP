resource "aws_iam_role" "glue_role" {
  name = "GlueS3RedshiftRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "glue_policy" {
  name = "dmp-glue-s3-athena"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.ngta_raw_bucket_name}",
          "arn:aws:s3:::${var.tsma_raw_bucket_name}",
          "arn:aws:s3:::${var.mapping_bucket_name}",
          "arn:aws:s3:::${var.price_books_bucket_name}",
          "arn:aws:s3:::${var.glue_assets_bucket_name}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.ngta_raw_bucket_name}/*",
          "arn:aws:s3:::${var.tsma_raw_bucket_name}/*",
          "arn:aws:s3:::${var.mapping_bucket_name}/*",
          "arn:aws:s3:::${var.price_books_bucket_name}/*",
          "arn:aws:s3:::${var.glue_assets_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:*",
          "athena:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "lambda_ngta_shared_role" {
  name = "lambda-ngta-telus-role-rachtis4"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_start_glue" {
  name = "dmp-lambda-start-glue"
  role = aws_iam_role.lambda_ngta_shared_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_shared_basic" {
  role       = aws_iam_role.lambda_ngta_shared_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "lambda_ngta_telus_quantities_role" {
  name = "lambda-ngta-telus-quantities-role-t2liebof"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_qty_start_glue" {
  name = "dmp-lambda-qty-start-glue"
  role = aws_iam_role.lambda_ngta_telus_quantities_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_qty_basic" {
  role       = aws_iam_role.lambda_ngta_telus_quantities_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "lambda_tsma_fact_role" {
  name = "lambda-tsma-fact-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_tsma_fact_inline" {
  name = "LambdaS3GlueAccess"
  role = aws_iam_role.lambda_tsma_fact_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetObjectTagging"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJob"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_tsma_fact_basic" {
  role       = aws_iam_role.lambda_tsma_fact_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "to_ec2_powerbi_athena_role" {
  name = "TO-EC2-PowerBI-Athena-Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "to_ec2_powerbi_athena_profile" {
  name = "TO-EC2-PowerBI-Athena-Role"
  role = aws_iam_role.to_ec2_powerbi_athena_role.name
}

resource "aws_iam_role_policy_attachment" "to_ec2_s3_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_glue_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_cloudwatch_agent" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "to_ec2_athena_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_ssm_ds" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMDirectoryServiceAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_ssm_core" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
