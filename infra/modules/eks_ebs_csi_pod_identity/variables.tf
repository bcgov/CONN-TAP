variable "cluster_arn" {
  type = string
}

variable "account_id" {
  type = string
}

variable "role_name" {
  type        = string
  description = "IAM role name for the EBS CSI controller (Pod Identity)."
}

variable "tags" {
  type    = map(string)
  default = {}
}
