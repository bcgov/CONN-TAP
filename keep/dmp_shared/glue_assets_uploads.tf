locals {
  lambda_zip_files = {
    lambda-ngta-rogers          = "${var.assets_local_dir}/lambda/lambda-ngta-rogers.zip"
    lambda-ngta-telus           = "${var.assets_local_dir}/lambda/lambda-ngta-telus.zip"
    lambda-ngta-telus-quantities = "${var.assets_local_dir}/lambda/lambda-ngta-telus-quantities.zip"
    lambda-tsma-fact            = "${var.assets_local_dir}/lambda/lambda-tsma-fact.zip"
    lambda-tsma-qsr             = "${var.assets_local_dir}/lambda/lambda-tsma-qsr.zip"
  }

  glue_script_files = {
    rogers_spend_ingestion               = "${var.assets_local_dir}/scripts/rogers_spend_ingestion.py"
    telus_spend_ingestion                = "${var.assets_local_dir}/scripts/telus_spend_ingestion.py"
    telus_quantities_ingestion           = "${var.assets_local_dir}/scripts/telus_quantities_ingestion.py"
    load-ngta-rogers-pricebook-notebook  = "${var.assets_local_dir}/scripts/load-ngta-rogers-pricebook-notebook.py"
    load-ngta-telus-pricebook-notebook   = "${var.assets_local_dir}/scripts/load-ngta-telus-pricebook-notebook.py"
    load-tsma-pricebook-notebook         = "${var.assets_local_dir}/scripts/load-tsma-pricebook-notebook.py"
    mapping-to-master                    = "${var.assets_local_dir}/scripts/mapping-to-master.py"
    move_tsma_files                      = "${var.assets_local_dir}/scripts/move_tsma_files.py"
    ngta-rogers-fact                     = "${var.assets_local_dir}/scripts/ngta-rogers-fact.py"
    ngta-telus-fact                      = "${var.assets_local_dir}/scripts/ngta-telus-fact.py"
    tsma-fact                            = "${var.assets_local_dir}/scripts/tsma-fact.py"
    tsma_fact                            = "${var.assets_local_dir}/scripts/tsma_fact.py"
    tsma-service-dashboard-data          = "${var.assets_local_dir}/scripts/tsma-service-dashboard-data.py"
    tsma_qsr_ingestion                   = "${var.assets_local_dir}/scripts/tsma_qsr_ingestion.py"
  }
}

resource "aws_s3_object" "lambda_zips" {
  for_each = local.lambda_zip_files

  bucket = var.glue_assets_bucket
  key    = "lambda/${each.key}.zip"
  source = each.value

  etag = filemd5(each.value)

  depends_on = [
    aws_s3_bucket.glue_assets
  ]
}

resource "aws_s3_object" "glue_scripts" {
  for_each = local.glue_script_files

  bucket = var.glue_assets_bucket
  key    = "scripts/${each.key}.py"
  source = each.value

  etag = filemd5(each.value)

  depends_on = [
    aws_s3_bucket.glue_assets
  ]
}