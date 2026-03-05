resource "aws_s3_bucket_notification" "ngta_raw_data_notifications" {
  bucket = "ngta-raw-data"

  # Rogers Spend
  lambda_function {
    id                  = "348ad04c-e242-4566-a9dd-3d597ff3b5c6"
    lambda_function_arn = data.aws_lambda_function.lambda_ngta_rogers.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "raw/rogers/spend_reports/"
    filter_suffix       = ".xlsx"
  }

  # Telus Spend
  lambda_function {
    id                  = "53164309-81dd-4358-a485-ea7f786987ad"
    lambda_function_arn = data.aws_lambda_function.lambda_ngta_telus.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload"]
    filter_prefix       = "raw/telus/spend_reports/"
    filter_suffix       = ".xlsx"
  }

  # Telus Quantities
  lambda_function {
    id                  = "2eac9bed-732b-4a72-9a35-97632603f139"
    lambda_function_arn = data.aws_lambda_function.lambda_ngta_telus_quantities.arn
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