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
  node_group_name                = "${var.license}-${var.env}"

  tags = {
    Environment = var.env
    License     = var.license
  }
}
