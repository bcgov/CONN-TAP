# EC2 role attachments (functional parity)
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

# TSMA Lambda role (new in test)
resource "aws_iam_role" "lambda_tsma_fact_role" {
  name = "lambda-tsma-fact-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_tsma_fact_basic" {
  role       = aws_iam_role.lambda_tsma_fact_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Let TSMA lambda read/write S3 and start Glue jobs (broad but functional)
resource "aws_iam_role_policy" "lambda_tsma_fact_inline" {
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
          "glue:GetJob"
        ],
        Resource = "*"
      }
    ]
  })
}