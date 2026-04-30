module "eks" {
  source = "../../modules/eks_cluster"

  cluster_name    = local.eks_cluster_name
  cluster_version = var.eks_cluster_version

  vpc_id              = data.aws_vpc.workload.id
  app_subnet_ids      = [data.aws_subnet.app_a.id, data.aws_subnet.app_b.id]
  node_instance_types = var.eks_node_instance_types
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  node_desired_size   = var.eks_node_desired_size

  cluster_endpoint_public_access = var.eks_cluster_endpoint_public_access

  tags = {
    Environment = var.env
    License     = var.license
  }
}

# Postgres RDS retained as the platform metadata DB. Only EKS workloads are
# permitted ingress; the SSM bastion has been removed along with Superset.
module "superset_rds" {
  source = "../../modules/superset_rds"

  name_prefix = local.rds_resource_prefix
  vpc_id      = data.aws_vpc.workload.id

  # Prod sizing: Multi-AZ standby (HA) + 1 readable async replica (read scaling).
  # The standby is not readable — replicas serve reporting/analytics offload.
  instance_class          = "db.t4g.medium"
  allocated_storage       = 50
  multi_az                = true
  read_replica_count      = 1
  backup_retention_period = 14
  deletion_protection     = true
  skip_final_snapshot     = false

  data_subnet_ids = [
    data.aws_subnet.data_a.id,
    data.aws_subnet.data_b.id,
  ]

  allowed_security_group_ids = {
    eks_node    = module.eks.node_security_group_id
    eks_cluster = module.eks.cluster_security_group_id
  }

  tags = {
    Environment = var.env
    License     = var.license
  }
}
