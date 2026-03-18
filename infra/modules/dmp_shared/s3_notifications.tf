resource "aws_lambda_permission" "allow_s3_invoke_rogers" {
  statement_id   = "${var.account_id}_event_permissions_from_${var.ngta_raw_bucket_name}_for_lambda-ngta-rogers"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_rogers.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket_name}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_telus" {
  statement_id   = "${var.account_id}_event_permissions_from_${var.ngta_raw_bucket_name}_for_lambda-ngta-telus"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_telus.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket_name}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_telus_quantities" {
  statement_id   = "lambda-${var.account_id}-event_permissions-${var.ngta_raw_bucket_name}-for-lambda-ngta-telus-quantities"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_ngta_telus_quantities.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.ngta_raw_bucket_name}"
  source_account = var.account_id
}

resource "aws_lambda_permission" "allow_s3_invoke_tsma_qsr" {
  statement_id   = "AllowS3InvokeTSMAQSR"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.lambda_tsma_qsr.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = "arn:aws:s3:::${var.tsma_raw_bucket_name}"
  source_account = var.account_id
}


resource "aws_s3_bucket_notification" "ngta_raw_data_notifications" {
  bucket = var.ngta_raw_bucket_name

  lambda_function {
    id                  = "rogers-spend"
    lambda_function_arn = aws_lambda_function.lambda_ngta_rogers.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "raw/rogers/spend_reports/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "telus-spend"
    lambda_function_arn = aws_lambda_function.lambda_ngta_telus.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "raw/telus/spend_reports/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    id                  = "telus-quantities"
    lambda_function_arn = aws_lambda_function.lambda_ngta_telus_quantities.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/telus/quantities_reports/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke_rogers,
    aws_lambda_permission.allow_s3_invoke_telus,
    aws_lambda_permission.allow_s3_invoke_telus_quantities
  ]
}

resource "aws_s3_bucket_notification" "tsma_raw_data_notifications" {
  bucket = var.tsma_raw_bucket_name

  lambda_function {
    id                  = "tsma-qsr"
    lambda_function_arn = aws_lambda_function.lambda_tsma_qsr.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "raw_quarterly_spend_report/"
    filter_suffix       = ".xlsx"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke_tsma_qsr
  ]
}