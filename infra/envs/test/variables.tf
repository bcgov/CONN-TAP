variable "aws_region" {
  type = string

  validation {
    condition     = var.aws_region == "ca-central-1"
    error_message = "This account is restricted to ca-central-1."
  }
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
