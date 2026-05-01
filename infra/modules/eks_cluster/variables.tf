variable "cluster_name" {
  type        = string
  description = "EKS cluster name (stable before apply; used by Kubernetes provider data sources)."
}

variable "cluster_version" {
  type        = string
  description = "Kubernetes version for the cluster."
}

variable "vpc_id" {
  type = string
}

variable "app_subnet_ids" {
  type        = list(string)
  description = "App-tier private subnet IDs (two AZs) for managed nodes and control-plane ENIs."
}

variable "cluster_endpoint_public_access" {
  type        = bool
  default     = true
  description = "If false, the API is only reachable from the VPC (align with LZA). May require two-step apply from inside the network."
}

variable "node_group_name" {
  type        = string
  description = "Name prefix for the managed node group. Recommend '{license}-{env}'."
}

variable "node_instance_types" {
  type    = list(string)
  default = ["m5.large"]
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "tags" {
  type    = map(string)
  default = {}
}
