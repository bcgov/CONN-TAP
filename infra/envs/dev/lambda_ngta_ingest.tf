module "ngta_ingest_lambda" {
  source = "../../modules/ngta_ingest_lambda"

  repo_root            = "${path.root}/../../.."
  ngta_raw_bucket_name = var.ngta_raw_bucket_name
  account_id           = data.aws_caller_identity.current.account_id

  db_password           = module.platform_rds.db_password
  rds_endpoint          = module.platform_rds.db_instance_address
  rds_db_name           = module.platform_rds.db_name
  rds_security_group_id = module.platform_rds.security_group_id

  vpc_id            = data.aws_vpc.workload.id
  lambda_subnet_ids = [data.aws_subnet.data_a.id, data.aws_subnet.data_b.id]

  dry_run = false
}
