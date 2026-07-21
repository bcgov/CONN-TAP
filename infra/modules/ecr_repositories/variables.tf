variable "name_prefix" {
  type        = string
  description = "Prefix for ECR repository names, typically '<license>-<env>-app'."
}

variable "repository_names" {
  type        = set(string)
  description = "Application image repository suffixes to create."

  validation {
    condition     = length(var.repository_names) > 0
    error_message = "At least one ECR repository name is required."
  }
}

variable "image_tag_mutability" {
  type        = string
  default     = "IMMUTABLE"
  description = "ECR image tag mutability setting. Use MUTABLE only where tags must be overwritten, such as dev."

  validation {
    condition     = contains(["IMMUTABLE", "MUTABLE"], var.image_tag_mutability)
    error_message = "image_tag_mutability must be either IMMUTABLE or MUTABLE."
  }
}

variable "untagged_image_expire_after_days" {
  type        = number
  default     = 14
  description = "Delete untagged images older than this many days."
}

variable "tagged_image_expire_after_days" {
  type        = number
  default     = null
  description = "When set, delete tagged images older than this many days. Use for immutable prod registries to expire stale release tags."
}

variable "tags" {
  type    = map(string)
  default = {}
}
