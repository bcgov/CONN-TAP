module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.31.6"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access  = var.cluster_endpoint_public_access
  cluster_endpoint_private_access = true

  # Opt out of extended support — clusters stay on standard (12-month) support
  # and must be upgraded before the version reaches end-of-standard-support.
  cluster_upgrade_policy = {
    support_type = "STANDARD"
  }

  vpc_id                   = var.vpc_id
  subnet_ids               = var.app_subnet_ids
  control_plane_subnet_ids = var.app_subnet_ids

  enable_irsa = false

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    eks-pod-identity-agent = {
      most_recent = true
    }
    # aws-ebs-csi-driver is declared as a standalone aws_eks_addon in each
    # environment's ebs_csi.tf with depends_on = [aws_eks_pod_identity_association.ebs_csi]
    # so Terraform guarantees the Pod Identity association exists before the
    # addon health-check runs.
  }

  eks_managed_node_groups = {
    (var.node_group_name) = {
      name                     = "${var.node_group_name}-ng"
      instance_types           = var.node_instance_types
      min_size                 = var.node_min_size
      max_size                 = var.node_max_size
      desired_size             = var.node_desired_size
      capacity_type            = "ON_DEMAND"
      iam_role_use_name_prefix = true
    }
  }

  tags = var.tags
}
