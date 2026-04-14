# =============================================================================
# EKS + Superset (LZA-aligned).
#
# Bootstrap: on a fresh account the Kubernetes/Helm data source may not exist
# until the cluster is created; run a first apply targeting AWS-only if needed:
#   terraform apply -target=module.eks -target=module.superset_rds -target=module.eks_alb_controller_identity
# then run a full apply for in-cluster resources.
#
# IP capacity: the LZA App tier is tight (/26 per AZ). EKS VPC CNI uses ENIs +
# secondary IPs on nodes. Right-size node counts and request a secondary CIDR
# early if you expect many pods.
#
# ACM: set superset_acm_certificate_arn (platform default or custom) before apply.
# =============================================================================

variable "eks_cluster_version" {
  type        = string
  default     = "1.33"
  description = "EKS Kubernetes version. Stay on a version in standard support to avoid extended-support control-plane pricing."
}

variable "eks_cluster_endpoint_public_access" {
  type        = bool
  default     = true
  description = "If false, kubectl/Helm must run from inside the VPC (or over private API access). LZA may require false in production."
}

variable "eks_node_instance_types" {
  type        = list(string)
  default     = ["m5.large"]
  description = "Managed node instance types; smaller types reduce ENI capacity per node (/24 App tier planning)."
}

variable "eks_node_min_size" {
  type    = number
  default = 2
}

variable "eks_node_max_size" {
  type    = number
  default = 4
}

variable "eks_node_desired_size" {
  type    = number
  default = 2
}

variable "lza_subnet_name_app_a" {
  type        = string
  default     = null
  description = "Override App subnet A Name tag; default is title(env)-App-A matching existing PowerBI pattern."
}

variable "lza_subnet_name_app_b" {
  type        = string
  default     = null
  description = "Override App subnet B Name tag; default is title(env)-App-B."
}

variable "lza_subnet_name_web_a" {
  type        = string
  default     = null
  description = "Override Web-MainTgwAttach subnet A Name tag."
}

variable "lza_subnet_name_web_b" {
  type        = string
  default     = null
  description = "Override Web-MainTgwAttach subnet B Name tag."
}

variable "lza_subnet_name_data_a" {
  type        = string
  default     = null
  description = "Override Data subnet A Name tag."
}

variable "lza_subnet_name_data_b" {
  type        = string
  default     = null
  description = "Override Data subnet B Name tag."
}

variable "superset_acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the internal ALB HTTPS listener (platform default internal.stratus or custom)."
}

variable "superset_ingress_host" {
  type        = string
  description = "FQDN for the Superset Ingress host (e.g. Stratus hostname)."
}

variable "ssm_bastion_instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 type for the SSM RDS bastion (App subnet; SSM port forward to PostgreSQL)."
}

variable "superset_helm_chart_version" {
  type        = string
  default     = "0.15.2"
  description = "Pin the apache/superset Helm chart version (appVersion tracks Superset, e.g. 0.15.2 -> 5.0.0)."
}

variable "superset_alb_controller_chart_version" {
  type        = string
  default     = "1.9.2"
  description = "Pin aws-load-balancer-controller chart version (eks-charts)."
}

variable "superset_init_admin_password" {
  type        = string
  sensitive   = true
  description = "Initial Superset admin password (rotate after first login)."
}

variable "superset_redis_password" {
  type        = string
  default     = null
  sensitive   = true
  description = "In-cluster Redis password (Bitnami subchart + supersetNode.connections). If null, Terraform generates one. From a .env file use: TF_VAR_superset_redis_password=... (same pattern as other TF_VAR_* inputs)."
}
