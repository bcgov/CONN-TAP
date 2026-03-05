resource "aws_lambda_function" "lambda_tsma_fact" {
  function_name = "lambda-tsma-fact"
  role          = aws_iam_role.lambda_tsma_fact_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket = var.glue_assets_bucket
  s3_key    = "lambda/lambda-tsma-fact.zip"

  environment {
    variables = {
      GLUE_JOB_NAME = "tsma-fact"
    }
  }
}