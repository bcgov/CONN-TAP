resource "aws_s3_object" "glue_scripts" {
  for_each = local.glue_scripts

  bucket = aws_s3_bucket.glue_assets.bucket
  key    = each.value.key
  source = each.value.source
  etag   = filemd5(each.value.source)
}

resource "aws_s3_object" "lambda_ngta_rogers_zip" {
  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = "lambda/lambda-ngta-rogers.zip"
  source       = "${path.module}/lambda-ngta-rogers.zip"
  etag         = filemd5("${path.module}/lambda-ngta-rogers.zip")
  content_type = "application/zip"

  lifecycle {
    ignore_changes = [
      etag,
      source
    ]
  }
}

resource "aws_s3_object" "lambda_ngta_telus_zip" {
  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = "lambda/lambda-ngta-telus.zip"
  source       = "${path.module}/lambda-ngta-telus.zip"
  etag         = filemd5("${path.module}/lambda-ngta-telus.zip")
  content_type = "application/zip"

  lifecycle {
    ignore_changes = [
      etag,
      source
    ]
  }
}

resource "aws_s3_object" "lambda_ngta_telus_quantities_zip" {
  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = "lambda/lambda-ngta-telus-quantities.zip"
  source       = "${path.module}/lambda-ngta-telus-quantities.zip"
  etag         = filemd5("${path.module}/lambda-ngta-telus-quantities.zip")
  content_type = "application/zip"

  lifecycle {
    ignore_changes = [
      etag,
      source
    ]
  }
}

resource "aws_s3_object" "lambda_tsma_fact_zip" {
  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = "lambda/lambda-tsma-fact.zip"
  source       = "${path.module}/lambda-tsma-fact.zip"
  etag         = filemd5("${path.module}/lambda-tsma-fact.zip")
  content_type = "application/zip"

  lifecycle {
    ignore_changes = [
      etag,
      source
    ]
  }
}

resource "aws_s3_object" "lambda_tsma_qsr_zip" {
  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = "lambda/lambda-tsma-qsr.zip"
  source       = "${path.module}/lambda-tsma-qsr.zip"
  etag         = filemd5("${path.module}/lambda-tsma-qsr.zip")
  content_type = "application/zip"

  lifecycle {
    ignore_changes = [
      etag,
      source
    ]
  }
}

resource "aws_s3_object" "lambda_zips" {
  for_each = local.lambda_zip_sources

  bucket       = aws_s3_bucket.glue_assets.bucket
  key          = each.value.key
  source       = each.value.source
  etag         = filemd5(each.value.source)
  content_type = "application/zip"
}