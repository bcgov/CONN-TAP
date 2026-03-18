resource "aws_s3_object" "glue_scripts" {
  for_each = local.glue_scripts

  bucket = var.glue_assets_bucket_name
  key    = each.value.key
  source = each.value.source
  etag   = filemd5(each.value.source)
}

# ---------------------------------------------------------------------------
# Lambda ZIPs — built from .py source files dropped into lambda/
# Each .py is packaged as lambda_function.py inside the ZIP to match the
# handler: lambda_function.lambda_handler
# ---------------------------------------------------------------------------

data "archive_file" "lambda_ngta_rogers" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/lambda_ngta_rogers.zip"
  source {
    content  = file("${var.assets_dir}/lambda/lambda_ngta_rogers.py")
    filename = "lambda_function.py"
  }
}

resource "aws_s3_object" "lambda_ngta_rogers_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_ngta_rogers.zip"
  source       = data.archive_file.lambda_ngta_rogers.output_path
  etag         = data.archive_file.lambda_ngta_rogers.output_md5
  content_type = "application/zip"
}

data "archive_file" "lambda_ngta_telus" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/lambda_ngta_telus.zip"
  source {
    content  = file("${var.assets_dir}/lambda/lambda_ngta_telus.py")
    filename = "lambda_function.py"
  }
}

resource "aws_s3_object" "lambda_ngta_telus_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_ngta_telus.zip"
  source       = data.archive_file.lambda_ngta_telus.output_path
  etag         = data.archive_file.lambda_ngta_telus.output_md5
  content_type = "application/zip"
}

data "archive_file" "lambda_ngta_telus_quantities" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/lambda_ngta_telus_quantities.zip"
  source {
    content  = file("${var.assets_dir}/lambda/lambda_ngta_telus_quantities.py")
    filename = "lambda_function.py"
  }
}

resource "aws_s3_object" "lambda_ngta_telus_quantities_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_ngta_telus_quantities.zip"
  source       = data.archive_file.lambda_ngta_telus_quantities.output_path
  etag         = data.archive_file.lambda_ngta_telus_quantities.output_md5
  content_type = "application/zip"
}

data "archive_file" "lambda_tsma_fact" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/lambda_tsma_fact.zip"
  source {
    content  = file("${var.assets_dir}/lambda/lambda_tsma_fact.py")
    filename = "lambda_function.py"
  }
}

resource "aws_s3_object" "lambda_tsma_fact_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_tsma_fact.zip"
  source       = data.archive_file.lambda_tsma_fact.output_path
  etag         = data.archive_file.lambda_tsma_fact.output_md5
  content_type = "application/zip"
}

data "archive_file" "lambda_tsma_qsr" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/lambda_tsma_qsr.zip"
  source {
    content  = file("${var.assets_dir}/lambda/lambda_tsma_qsr.py")
    filename = "lambda_function.py"
  }
}

resource "aws_s3_object" "lambda_tsma_qsr_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_tsma_qsr.zip"
  source       = data.archive_file.lambda_tsma_qsr.output_path
  etag         = data.archive_file.lambda_tsma_qsr.output_md5
  content_type = "application/zip"
}
