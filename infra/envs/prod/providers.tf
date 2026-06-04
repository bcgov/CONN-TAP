terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.81, < 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.14"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_eks_cluster" "kube" {
  name       = local.eks_cluster_name
  depends_on = [terraform_data.eks_control_plane_ready]
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.kube.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.kube.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks", "get-token",
      "--cluster-name", data.aws_eks_cluster.kube.name,
      "--region", var.aws_region,
    ]
  }
}

provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.kube.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.kube.certificate_authority[0].data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks", "get-token",
        "--cluster-name", data.aws_eks_cluster.kube.name,
        "--region", var.aws_region,
      ]
    }
  }
}
