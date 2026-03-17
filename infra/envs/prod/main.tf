locals {
  ngta_raw_bucket_name    = "${var.license}-${var.env}-ngta-raw-data"
  tsma_raw_bucket_name    = "${var.license}-${var.env}-tsma-raw-data"
  mapping_bucket_name     = "${var.license}-${var.env}-tsma-ngta-mapping"
  price_books_bucket_name = "${var.license}-${var.env}-tsma-ngta-price-books"
  glue_assets_bucket_name = "${var.license}-${var.env}-glue-assets"

  vpc_name        = title(var.env)
  ec2_subnet_name = "${title(var.env)}-App-A"

  powerbi_key_name      = "${var.license}-${var.env}-powerbi-key"
  powerbi_instance_name = "${var.license}-${var.env}-ec2-powerbi"

  ec2_public_key = file("public-${var.env}.pub")
}

module "ngta_raw_data" {
  source = "../../modules/s3_bucket"

  bucket_name       = local.ngta_raw_bucket_name
  enable_versioning = false
}

module "tsma_raw_data" {
  source = "../../modules/s3_bucket"

  bucket_name       = local.tsma_raw_bucket_name
  enable_versioning = false
}

module "tsma_ngta_mapping" {
  source = "../../modules/s3_bucket"

  bucket_name       = local.mapping_bucket_name
  enable_versioning = false
}

module "tsma_ngta_price_books" {
  source = "../../modules/s3_bucket"

  bucket_name       = local.price_books_bucket_name
  enable_versioning = false
}

module "glue_assets" {
  source = "../../modules/s3_bucket"

  bucket_name       = local.glue_assets_bucket_name
  enable_versioning = false
}

data "aws_caller_identity" "current" {}

module "dmp" {
  source = "../../modules/dmp_shared"

  aws_region = var.aws_region
  env        = var.env
  account_id = data.aws_caller_identity.current.account_id

  ngta_raw_bucket_name    = local.ngta_raw_bucket_name
  tsma_raw_bucket_name    = local.tsma_raw_bucket_name
  mapping_bucket_name     = local.mapping_bucket_name
  price_books_bucket_name = local.price_books_bucket_name
  glue_assets_bucket_name = local.glue_assets_bucket_name

  vpc_name                 = local.vpc_name
  ec2_subnet_name          = local.ec2_subnet_name
  ec2_security_group_names = var.ec2_security_group_names

  powerbi_key_name      = local.powerbi_key_name
  ec2_public_key        = local.ec2_public_key
  powerbi_instance_name = local.powerbi_instance_name
  powerbi_instance_type = var.powerbi_instance_type
  powerbi_ami_id        = var.powerbi_ami_id
  powerbi_alert_email   = var.powerbi_alert_email

  assets_dir = var.assets_dir

  depends_on = [
    module.ngta_raw_data,
    module.tsma_raw_data,
    module.tsma_ngta_mapping,
    module.tsma_ngta_price_books,
    module.glue_assets,
  ]
}
