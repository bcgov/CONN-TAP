# SSM bastion for port-forwarding to the platform Postgres RDS.
# No inbound traffic — access is via AWS Systems Manager Session Manager only.
# In LZA this belongs in the Management subnet tier.
# Although the docs, specify bastion hosts should go on management, connection was not possible from this subnet to Data subnet.
module "postgres_bastion" {
  source = "../../modules/ssm_rds_bastion"

  name_prefix = local.rds_resource_prefix
  vpc_id      = data.aws_vpc.workload.id
  # subnet_id     = data.aws_subnet.management_a.id
  subnet_id     = data.aws_subnet.app_a.id
  instance_type = "t3.micro"

  tags = {
    Environment = var.env
    License     = var.license
  }
}

module "platform_rds" {
  source = "../../modules/postgres_rds"

  name_prefix = local.rds_resource_prefix
  vpc_id      = data.aws_vpc.workload.id

  # Platform Postgres RDS. Ingress is restricted to EKS workloads and the SSM bastion.
  instance_class    = "db.t4g.small"
  allocated_storage = 20

  data_subnet_ids = [
    data.aws_subnet.data_a.id,
    data.aws_subnet.data_b.id,
  ]

  allowed_security_group_ids = {
    eks_node         = module.eks.node_security_group_id
    eks_cluster      = module.eks.cluster_security_group_id
    postgres_bastion = module.postgres_bastion.security_group_id
  }

  tags = {
    Environment = var.env
    License     = var.license
  }
}
