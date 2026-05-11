module "ebs_csi_pod_identity" {
  source = "../../modules/eks_ebs_csi_pod_identity"

  cluster_arn = module.eks.cluster_arn
  account_id  = data.aws_caller_identity.current.account_id
  role_name   = "${var.license}-${var.env}-ebs-csi"

  tags = {
    Environment = var.env
    License     = var.license
  }
}

resource "aws_eks_pod_identity_association" "ebs_csi" {
  cluster_name    = local.eks_cluster_name
  namespace       = "kube-system"
  service_account = "ebs-csi-controller-sa"
  role_arn        = module.ebs_csi_pod_identity.role_arn
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name                = local.eks_cluster_name
  addon_name                  = "aws-ebs-csi-driver"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  configuration_values = jsonencode({
    controller = {
      env = [
        {
          name  = "AWS_EC2_METADATA_DISABLED"
          value = "true"
        }
      ]
    }
  })

  tags = {
    Environment = var.env
    License     = var.license
  }

  depends_on = [aws_eks_pod_identity_association.ebs_csi]
}
