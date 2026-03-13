resource "aws_s3_bucket" "glue_assets" {
  bucket = var.glue_assets_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "glue_assets" {
  bucket                  = aws_s3_bucket.glue_assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "glue_assets" {
  bucket = aws_s3_bucket.glue_assets.id

  rule {
    bucket_key_enabled = false

    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}