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

  # Single PostgreSQL instance, single-AZ, no read replicas. The module does not
  # create a replica or set multi_az; defaults are pinned here for clarity.
  instance_class    = "db.t4g.small"
  allocated_storage = 20

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
