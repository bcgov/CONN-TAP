# =============================================================================
# EKS + RDS + LZA internal ALB (AWS Load Balancer Controller).
#
# Bootstrap: on a fresh account the Kubernetes/Helm providers may not work until
# the cluster exists; run a targeted apply first if needed:
#   terraform apply -target=module.eks -target=module.eks_alb_controller_identity
# then run a full apply for in-cluster resources.
#
# ACM: set internal_acm_certificate_arn (platform Stratus wildcard or custom).
# =============================================================================

variable "eks_cluster_version" {
  type        = string
  default     = "1.34"
  description = "EKS Kubernetes version."
}

variable "eks_cluster_endpoint_public_access" {
  type        = bool
  default     = true
  description = "If false, kubectl must run from inside the VPC (or over private API access)."
}

variable "eks_node_instance_types" {
  type        = list(string)
  default     = ["m5.large"]
  description = "Managed node instance types."
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
  description = "Override App subnet A Name tag; default is title(env)-App-A."
}

variable "lza_subnet_name_app_b" {
  type        = string
  default     = null
  description = "Override App subnet B Name tag; default is title(env)-App-B."
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

variable "lza_subnet_name_management_a" {
  type        = string
  default     = null
  description = "Override Management subnet A Name tag."
}

variable "lza_subnet_name_management_b" {
  type        = string
  default     = null
  description = "Override Management subnet B Name tag."
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

variable "internal_acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the internal ALB HTTPS listener (platform Stratus wildcard or custom)."
}

variable "alb_controller_chart_version" {
  type        = string
  default     = "1.9.2"
  description = "Pin aws-load-balancer-controller chart version (eks-charts)."
}
