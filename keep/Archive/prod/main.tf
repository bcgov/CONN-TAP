module "ngta_raw_data" {
  source = "../../modules/s3_bucket"
  name   = var.ngta_raw_bucket
}

module "tsma_raw_data" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_raw_bucket
}

module "tsma_ngta_mapping" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_ngta_mapping_bucket
}

module "tsma_ngta_price_books" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_ngta_price_books_bucket
}

module "dmp" {
  source = "../../modules/dmp_shared"

  aws_region = var.aws_region
  account_id = var.account_id

  vpc_id        = var.vpc_id
  ec2_subnet_id = var.ec2_subnet_id

  ec2_security_group_ids = var.ec2_security_group_ids

  glue_assets_bucket    = var.glue_assets_bucket
  athena_results_prefix = var.athena_results_prefix

  ngta_raw_bucket              = var.ngta_raw_bucket
  tsma_raw_bucket              = var.tsma_raw_bucket
  tsma_ngta_mapping_bucket     = var.tsma_ngta_mapping_bucket
  tsma_ngta_price_books_bucket = var.tsma_ngta_price_books_bucket

  powerbi_ami      = var.powerbi_ami
  powerbi_key_name = var.powerbi_key_name

  ec2_instance_profile_name = var.ec2_instance_profile_name
  ec2_key_name              = var.ec2_key_name
  ec2_public_key            = var.ec2_public_key

  enable_redshift             = var.enable_redshift
  redshift_cluster_identifier = var.redshift_cluster_identifier
  redshift_node_type          = var.redshift_node_type
  redshift_master_username    = var.redshift_master_username
  redshift_database_name      = var.redshift_database_name
  redshift_subnet_ids         = var.redshift_subnet_ids
  redshift_security_group_id  = var.redshift_security_group_id

  enable_tsma_lambda_fact = var.enable_tsma_lambda_fact

  assets_local_dir = "${path.module}/_glue_assets"

  # IMPORTANT: ensure bucket resources exist before the shared module tries
  # to create S3 notifications pointing at them.
  depends_on = [
    module.ngta_raw_data,
    module.tsma_raw_data,
    module.tsma_ngta_mapping,
    module.tsma_ngta_price_books,
  ]
}