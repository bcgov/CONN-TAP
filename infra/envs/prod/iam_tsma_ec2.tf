# TSMA + EC2 + Trigger IAM roles
resource "aws_iam_role" "lambda_tsma_fact_role" {
  name = "lambda-tsma-fact-role-yyffbk05"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "lambda_tsma_raw_role" {
  name = "lambda-tsma-raw-role-sahho2ng"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "lambda_tsma_role" {
  name = "lambda-tsma-role-fr3szlk6"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "to_ec2_powerbi_athena_role" {
  name        = "TO-EC2-PowerBI-Athena-Role"
  description = "Allows EC2 instances to call AWS services on your behalf."

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

resource "aws_iam_role" "trigger_glue_on_s3_event_role" {
  name = "trigger-glue-on-s3-event-role-dz8ymzxe"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  # Keep AWS-managed fields stable
  lifecycle {
    ignore_changes = [
      description,
      tags
    ]
  }
}

# TSMA Lambda roles (account-managed Lambda basic exec policies)
resource "aws_iam_role_policy_attachment" "lambda_tsma_fact_basic" {
  role       = aws_iam_role.lambda_tsma_fact_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/service-role/AWSLambdaBasicExecutionRole-ebb0f300-9d54-4a2d-8c6b-23ea7dad00de"
}

resource "aws_iam_role_policy_attachment" "lambda_tsma_raw_basic" {
  role       = aws_iam_role.lambda_tsma_raw_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/service-role/AWSLambdaBasicExecutionRole-17df2d65-df0d-4227-bf88-ac533624b73a"
}

resource "aws_iam_role_policy_attachment" "lambda_tsma_basic" {
  role       = aws_iam_role.lambda_tsma_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/service-role/AWSLambdaBasicExecutionRole-6c8e19ed-259b-4c63-b6ca-bf6966386928"
}

# Trigger role policies (account-managed)
resource "aws_iam_role_policy_attachment" "trigger_vpc_access" {
  role       = aws_iam_role.trigger_glue_on_s3_event_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/service-role/AWSLambdaVPCAccessExecutionRole-24572427-4fe0-40de-a6d3-74427bcf641c"
}

resource "aws_iam_role_policy_attachment" "trigger_basic_exec" {
  role       = aws_iam_role.trigger_glue_on_s3_event_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/service-role/AWSLambdaBasicExecutionRole-d9dfb508-3212-4bb2-ad95-1b6d34e43c94"
}

# EC2 PowerBI role managed policies
resource "aws_iam_role_policy_attachment" "to_ec2_cloudwatch_agent" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "to_ec2_ssm_ds" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMDirectoryServiceAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_ssm_core" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "to_ec2_glue_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_athena_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_s3_full" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "to_ec2_pbmm_ssm_write" {
  role       = aws_iam_role.to_ec2_powerbi_athena_role.name
  policy_arn = "arn:aws:iam::585768151939:policy/PBMMAccel-SSMWriteAccessPolicy-2C3CEBE0"
}


# Inline policy (TSMA fact role)
resource "aws_iam_role_policy" "lambda_tsma_fact_inline_s3_glue" {
  name = "LambdaS3GlueAccess"
  role = aws_iam_role.lambda_tsma_fact_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetObjectTagging"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJob",
          "glue:BatchGetJobs",
          "glue:BatchGetWorkflows"
        ],
        Resource = "*"
      }
    ]
  })
}

# Instance profile for the PowerBI EC2 instance
resource "aws_iam_instance_profile" "to_ec2_powerbi_athena_profile" {
  name = "TO-EC2-PowerBI-Athena-Role"
  role = aws_iam_role.to_ec2_powerbi_athena_role.name
}