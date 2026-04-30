variable "aws_region" {
  type = string
}

variable "license" {
  type        = string
  description = "License plate prefix used to namespace all resource names (e.g. abc123)."
}

variable "env" {
  type = string
}

variable "account_id" {
  type    = string
  default = null
}
