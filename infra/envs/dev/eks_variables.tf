# =============================================================================
# EKS + RDS only. Superset, ALB controller, SSM bastion, and DMP shared
# resources have been removed from this environment.
# =============================================================================

variable "eks_cluster_version" {
  type        = string
  default     = "1.33"
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
