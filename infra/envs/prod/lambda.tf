data "aws_lambda_function" "lambda_ngta_rogers" {
  function_name = "lambda-ngta-rogers"
}

data "aws_lambda_function" "lambda_ngta_telus" {
  function_name = "lambda-ngta-telus"
}

data "aws_lambda_function" "lambda_ngta_telus_quantities" {
  function_name = "lambda-ngta-telus-quantities"
}


# Allow S3 bucket to invoke each Lambda
resource "aws_lambda_permission" "allow_s3_invoke_rogers" {
  statement_id   = "585768151939_event_permissions_from_ngta-raw-data_for_lambda-ngta-rogers"
  action         = "lambda:InvokeFunction"
  function_name  = data.aws_lambda_function.lambda_ngta_rogers.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::ngta-raw-data"
  source_account = "585768151939"
}

resource "aws_lambda_permission" "allow_s3_invoke_telus" {
  statement_id   = "585768151939_event_permissions_from_ngta-raw-data_for_lambda-ngta-telus"
  action         = "lambda:InvokeFunction"
  function_name  = data.aws_lambda_function.lambda_ngta_telus.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::ngta-raw-data"
  source_account = "585768151939"
}

resource "aws_lambda_permission" "allow_s3_invoke_telus_quantities" {
  statement_id   = "lambda-ca631277-5d9f-4eb6-a482-60d8d70586fc"
  action         = "lambda:InvokeFunction"
  function_name  = data.aws_lambda_function.lambda_ngta_telus_quantities.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::ngta-raw-data"
  source_account = "585768151939"
}