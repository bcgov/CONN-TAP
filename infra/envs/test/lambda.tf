resource "aws_lambda_function" "lambda_ngta_rogers" {
  function_name = "lambda-ngta-rogers"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket = var.glue_assets_bucket
  s3_key    = "lambda/lambda-ngta-rogers.zip"
  environment {
    variables = {
      ROGERS_GLUE_JOB = "rogers_spend_ingestion"
    }
  }
}

resource "aws_lambda_function" "lambda_ngta_telus" {
  function_name = "lambda-ngta-telus"
  role          = aws_iam_role.lambda_ngta_shared_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket = var.glue_assets_bucket
  s3_key    = "lambda/lambda-ngta-telus.zip"
  environment {
    variables = {
      GLUE_JOB_NAME = "telus_spend_ingestion"
    }
  }
}

resource "aws_lambda_function" "lambda_ngta_telus_quantities" {
  function_name = "lambda-ngta-telus-quantities"
  role          = aws_iam_role.lambda_ngta_telus_quantities_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  s3_bucket = var.glue_assets_bucket
  s3_key    = "lambda/lambda-ngta-telus-quantities.zip"
  environment {
    variables = {
      GLUE_JOB_NAME = "telus_quantities_ingestion"
    }
  }
}

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
