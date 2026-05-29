# LZA Pattern A: internal ALB via AWS Load Balancer Controller (Pod Identity, not IRSA).
# /bcgovhealthcheck is a fixed-response rule on the shared ingress group; conn-tap app
# ingress is deployed by GitHub Actions (helm/conn-tap) into the same group.

resource "terraform_data" "eks_control_plane_ready" {
  input = module.eks.cluster_arn
}

module "eks_alb_controller_identity" {
  source = "../../modules/eks_alb_controller_identity"

  cluster_arn      = module.eks.cluster_arn
  account_id       = data.aws_caller_identity.current.account_id
  role_name        = "${var.license}-${var.env}-eks-alb-controller"
  policy_file_path = "${path.module}/../../modules/eks_cluster/policies/aws-load-balancer-controller-iam.json"

  tags = {
    Environment = var.env
    License     = var.license
  }
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

  depends_on = [terraform_data.eks_control_plane_ready]
}

resource "aws_eks_pod_identity_association" "alb_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = kubernetes_service_account.alb_controller.metadata[0].name
  role_arn        = module.eks_alb_controller_identity.role_arn

  depends_on = [kubernetes_service_account.alb_controller]
}

resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = var.alb_controller_chart_version
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

# LZA perimeter probe: fixed HTTP 200 on /bcgovhealthcheck (shared IngressGroup with conn-tap).
resource "kubernetes_ingress_v1" "bcgov_healthcheck" {
  metadata {
    name      = "bcgovhealthcheck"
    namespace = "kube-system"
    annotations = {
      "alb.ingress.kubernetes.io/scheme"          = "internal"
      "alb.ingress.kubernetes.io/target-type"     = "ip"
      "alb.ingress.kubernetes.io/subnets"         = local.web_subnet_ids_csv
      "alb.ingress.kubernetes.io/certificate-arn" = var.internal_acm_certificate_arn
      "alb.ingress.kubernetes.io/group.name"      = local.internal_ingress_group
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

  depends_on = [helm_release.aws_load_balancer_controller]
}
