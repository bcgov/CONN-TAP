module "ngta_raw_data" {
  source = "../../modules/s3_bucket"

  bucket_name       = var.ngta_raw_bucket_name
  enable_versioning = false
}

module "tsma_raw_data" {
  source = "../../modules/s3_bucket"

  bucket_name       = var.tsma_raw_bucket_name
  enable_versioning = false
}

module "tsma_ngta_mapping" {
  source = "../../modules/s3_bucket"

  bucket_name       = var.mapping_bucket_name
  enable_versioning = false
}

module "tsma_ngta_price_books" {
  source = "../../modules/s3_bucket"

  bucket_name       = var.price_books_bucket_name
  enable_versioning = false
}

data "aws_caller_identity" "current" {}

module "dmp" {
  source = "../../modules/dmp_shared"

  aws_region = var.aws_region
  env        = var.env
  account_id = data.aws_caller_identity.current.account_id


  ngta_raw_bucket_name    = var.ngta_raw_bucket_name
  tsma_raw_bucket_name    = var.tsma_raw_bucket_name
  mapping_bucket_name     = var.mapping_bucket_name
  price_books_bucket_name = var.price_books_bucket_name
  glue_assets_bucket_name = var.glue_assets_bucket_name

  vpc_name                 = var.vpc_name
  ec2_subnet_name          = var.ec2_subnet_name
  ec2_security_group_names = var.ec2_security_group_names

  powerbi_key_name      = var.powerbi_key_name
  ec2_public_key        = var.ec2_public_key
  powerbi_instance_name = var.powerbi_instance_name
  powerbi_instance_type = var.powerbi_instance_type
  powerbi_ami_id        = var.powerbi_ami_id
  
  assets_dir            = var.assets_dir
}