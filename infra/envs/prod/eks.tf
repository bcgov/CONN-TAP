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

# Depends only on the EKS control plane (via cluster_arn), not on managed add-on
# health. Avoids deadlocks with EBS CSI + Pod Identity (see test/eks.tf).
resource "terraform_data" "eks_control_plane_ready" {
  input = module.eks.cluster_arn
}

module "ssm_rds_bastion" {
  source = "../../modules/ssm_rds_bastion"

  name_prefix   = local.superset_resource_prefix
  vpc_id        = data.aws_vpc.workload.id
  subnet_id     = data.aws_subnet.app_a.id
  instance_type = var.ssm_bastion_instance_type

  tags = {
    Environment = var.env
    License     = var.license
  }
}

module "superset_rds" {
  source = "../../modules/superset_rds"

  name_prefix = local.superset_resource_prefix
  vpc_id      = data.aws_vpc.workload.id

  data_subnet_ids = [
    data.aws_subnet.data_a.id,
    data.aws_subnet.data_b.id,
  ]

  allowed_security_group_ids = compact([
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
    module.ssm_rds_bastion.security_group_id,
  ])

  tags = {
    Environment = var.env
    License     = var.license
  }
}

module "eks_alb_controller_identity" {
  source = "../../modules/eks_alb_controller_identity"

  cluster_arn      = module.eks.cluster_arn
  account_id       = data.aws_caller_identity.current.account_id
  role_name        = "${var.license}-${var.env}-eks-alb-controller"
  policy_file_path = "${path.module}/../../modules/eks_cluster/policies/aws-load-balancer-controller-iam.json"
  tags             = { Environment = var.env, License = var.license }
}

resource "kubernetes_service_account" "alb_controller" {
  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"
    labels = {
      "app.kubernetes.io/name"      = "aws-load-balancer-controller"
      "app.kubernetes.io/component" = "controller"
    }
  }
}

resource "aws_eks_pod_identity_association" "alb_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = kubernetes_service_account.alb_controller.metadata[0].name
  role_arn        = module.eks_alb_controller_identity.role_arn
  depends_on      = [kubernetes_service_account.alb_controller]
}

# EBS CSI controller (managed add-on) uses SA ebs-csi-controller-sa; with IRSA
# disabled it otherwise inherits the node role and lacks EC2/EBS API coverage.
module "eks_ebs_csi_pod_identity" {
  source      = "../../modules/eks_ebs_csi_pod_identity"
  cluster_arn = module.eks.cluster_arn
  account_id  = data.aws_caller_identity.current.account_id
  role_name   = "${var.license}-${var.env}-eks-ebs-csi"
  tags        = { Environment = var.env, License = var.license }
}

resource "aws_eks_pod_identity_association" "ebs_csi_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = "ebs-csi-controller-sa"
  role_arn        = module.eks_ebs_csi_pod_identity.role_arn
}

resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = var.superset_alb_controller_chart_version
  namespace  = "kube-system"

  set {
    name  = "clusterName"
    value = module.eks.cluster_name
  }
  set {
    name  = "serviceAccount.create"
    value = "false"
  }
  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }
  set {
    name  = "region"
    value = var.aws_region
  }
  set {
    name  = "vpcId"
    value = data.aws_vpc.workload.id
  }

  depends_on = [
    terraform_data.eks_control_plane_ready,
    aws_eks_pod_identity_association.alb_controller,
  ]
}

resource "random_password" "superset_secret_key" {
  length  = 64
  special = false
}

resource "random_password" "superset_redis" {
  count   = var.superset_redis_password == null ? 1 : 0
  length  = 24
  special = false
}

locals {
  superset_redis_password = var.superset_redis_password != null ? var.superset_redis_password : random_password.superset_redis[0].result
}

data "aws_secretsmanager_secret_version" "superset_db" {
  secret_id = module.superset_rds.secret_arn
  depends_on = [
    module.superset_rds,
  ]
}

locals {
  # Secrets as second Helm values doc (see test/eks.tf — avoids set_sensitive apply drift).
  superset_sensitive_values_yaml = yamlencode({
    supersetNode = {
      connections = {
        db_pass        = data.aws_secretsmanager_secret_version.superset_db.secret_string
        redis_password = local.superset_redis_password
      }
    }
    extraSecretEnv = {
      SUPERSET_SECRET_KEY = random_password.superset_secret_key.result
    }
    init = {
      adminUser = {
        password = var.superset_init_admin_password
      }
    }
    redis = {
      auth = {
        password = local.superset_redis_password
      }
    }
  })
}

resource "kubernetes_namespace" "superset" {
  metadata {
    name = "superset"
    labels = {
      environment = var.env
    }
  }
}

# LZA perimeter probe: fixed HTTP 200 on /bcgovhealthcheck (same IngressGroup as Superset → one internal ALB).
# See: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/#actions
resource "kubernetes_ingress_v1" "bcgov_healthcheck" {
  metadata {
    name      = "bcgovhealthcheck"
    namespace = kubernetes_namespace.superset.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"          = "internal"
      "alb.ingress.kubernetes.io/target-type"     = "ip"
      "alb.ingress.kubernetes.io/subnets"         = local.web_subnet_ids_csv
      "alb.ingress.kubernetes.io/certificate-arn" = var.superset_acm_certificate_arn
      "alb.ingress.kubernetes.io/group.name"      = local.superset_ingress_group
      "alb.ingress.kubernetes.io/tags"            = "Public=True"
      "alb.ingress.kubernetes.io/listen-ports"    = jsonencode([{ HTTPS = 443 }])
      "alb.ingress.kubernetes.io/actions.bcgov-healthcheck" = jsonencode({
        Type = "fixed-response"
        FixedResponseConfig = {
          ContentType = "text/plain"
          MessageBody = "ok"
          StatusCode  = "200"
        }
      })
    }
  }

  spec {
    ingress_class_name = "alb"
    rule {
      http {
        path {
          path      = "/bcgovhealthcheck"
          path_type = "Exact"
          backend {
            service {
              name = "bcgov-healthcheck"
              port {
                name = "use-annotation"
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    helm_release.aws_load_balancer_controller,
    kubernetes_namespace.superset,
  ]
}

resource "helm_release" "superset" {
  name       = "superset"
  repository = "https://apache.github.io/superset"
  chart      = "superset"
  version    = var.superset_helm_chart_version
  namespace  = kubernetes_namespace.superset.metadata[0].name

  values = [
    templatefile("${path.module}/templates/superset-values.yaml.tftpl", {
      superset_ingress_host = var.superset_ingress_host
      web_subnet_ids_csv    = local.web_subnet_ids_csv
      acm_certificate_arn   = var.superset_acm_certificate_arn
      ingress_group_name    = local.superset_ingress_group
      db_host               = module.superset_rds.db_instance_address
      db_user               = module.superset_rds.db_username
      db_name               = module.superset_rds.db_name
      redis_host            = "superset-redis-headless"
    }),
    local.superset_sensitive_values_yaml,
  ]

  depends_on = [
    helm_release.aws_load_balancer_controller,
    module.superset_rds,
    kubernetes_namespace.superset,
    kubernetes_ingress_v1.bcgov_healthcheck,
  ]
}
