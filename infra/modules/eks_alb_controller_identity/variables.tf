variable "cluster_arn" {
  type = string
}

variable "account_id" {
  type = string
}

variable "role_name" {
  type        = string
  description = "IAM role name for the AWS Load Balancer Controller (Pod Identity)."
}

variable "policy_file_path" {
  type        = string
  description = "Path to aws-load-balancer-controller IAM policy JSON."
}

variable "tags" {
  type    = map(string)
  default = {}
}
