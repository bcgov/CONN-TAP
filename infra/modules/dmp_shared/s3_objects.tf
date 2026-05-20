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

# ---------------------------------------------------------------------------
# DMP Ingest Lambda (S3 → Postgres) — single dispatcher for all feed types.
# Terraform builds the dependency layer via pip install during apply.
# CI/CD only needs to run: terraform apply
# ---------------------------------------------------------------------------

locals {
  ngta_ingest_dir  = "${var.assets_dir}/lambda/ngta_ingest"
  dmp_layer_zip   = "${var.assets_dir}/lambda/ngta_ingest/ngta_ingest_layer.zip"
  dmp_layer_build = "${var.assets_dir}/lambda/ngta_ingest/layer_build"
}

resource "null_resource" "ngta_ingest_layer_build" {
  triggers = {
    requirements = filemd5("${local.ngta_ingest_dir}/requirements.txt")
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      rm -rf "${local.dmp_layer_build}"
      mkdir -p "${local.dmp_layer_build}/python"
      pip install \
        --requirement "${local.ngta_ingest_dir}/requirements.txt" \
        --target "${local.dmp_layer_build}/python" \
        --no-cache-dir \
        --quiet
      cd "${local.dmp_layer_build}" && zip -r "${local.dmp_layer_zip}" python/ --quiet
      rm -rf "${local.dmp_layer_build}"
    EOT
  }
}

resource "aws_s3_object" "ngta_ingest_layer_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/ngta_ingest_layer.zip"
  source       = local.dmp_layer_zip
  etag         = try(filemd5(local.dmp_layer_zip), "")
  content_type = "application/zip"
  depends_on   = [null_resource.ngta_ingest_layer_build]
}

data "archive_file" "lambda_ngta_ingest" {
  type        = "zip"
  output_path = "${var.assets_dir}/lambda/ngta_ingest/lambda_ngta_ingest.zip"

  source {
    content  = file("${local.ngta_ingest_dir}/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${var.assets_dir}/local_dev/raw_ingestion/tsma_postgres_ingest/ingest_tsma_excel_folder.py")
    filename = "ingest_tsma_excel_folder.py"
  }

  source {
    content  = file("${var.assets_dir}/local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py")
    filename = "ingest_raw_excel_folder.py"
  }

  source {
    content  = file("${var.assets_dir}/local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py")
    filename = "ingest_tsma_other_excel_folder.py"
  }
}

resource "aws_s3_object" "lambda_ngta_ingest_zip" {
  bucket       = var.glue_assets_bucket_name
  key          = "lambda/lambda_ngta_ingest.zip"
  source       = data.archive_file.lambda_ngta_ingest.output_path
  etag         = data.archive_file.lambda_ngta_ingest.output_md5
  content_type = "application/zip"
}
