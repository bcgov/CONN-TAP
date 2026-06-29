# Raw data landing bucket + S3-triggered Lambda that ingests into platform Postgres (raw_data).
# Upload source files via the AWS Console under the prefixes documented in lambda/ngta_ingest/handler.py.

locals {
  raw_data_bucket_name = "${var.license}-${var.env}-raw-data"
}

module "raw_data_bucket" {
  source = "../../modules/s3_bucket"

  bucket_name = local.raw_data_bucket_name
}

module "ngta_ingest_lambda" {
  source = "../../modules/ngta_ingest_lambda"

  name_prefix          = local.rds_resource_prefix
  repo_root            = abspath("${path.root}/../../..")
  ngta_raw_bucket_name = module.raw_data_bucket.bucket_name
  account_id           = data.aws_caller_identity.current.account_id

  db_password           = module.platform_rds.db_password
  rds_endpoint          = module.platform_rds.db_instance_address
  rds_db_name           = module.platform_rds.db_name
  rds_security_group_id = module.platform_rds.security_group_id

  vpc_id            = data.aws_vpc.workload.id
  lambda_subnet_ids = [data.aws_subnet.data_a.id, data.aws_subnet.data_b.id]

  dry_run = false

  depends_on = [module.raw_data_bucket]
}
