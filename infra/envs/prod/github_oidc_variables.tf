variable "github_owner" {
  type        = string
  default     = "bcgov"
  description = "GitHub organization or user that owns the repository."
}

variable "github_repository" {
  type        = string
  default     = "CONN-TAP"
  description = "GitHub repository name (without owner prefix)."
}

variable "github_actions_allowed_subjects" {
  type        = list(string)
  default     = null
  description = <<-EOT
    Optional explicit list of token sub claims permitted by the GitHub Actions trust policy
    (StringLike). When null, prod defaults restrict to the main branch and the
    'prod' GitHub Environment. Override to broaden or further restrict.
  EOT
}

variable "github_actions_create_oidc_provider" {
  type        = bool
  default     = false
  description = "Create the account-level GitHub OIDC provider. Set false if one already exists in this AWS account."
}

variable "github_actions_role_name" {
  type        = string
  default     = null
  description = "Override the GitHub Actions role name. Defaults to '<license>-<env>-github-actions'."
}

variable "github_actions_managed_policy_arns" {
  type        = list(string)
  default     = ["arn:aws:iam::aws:policy/AdministratorAccess"]
  description = "Managed policy ARNs attached to the GitHub Actions role. Default grants full admin (Terraform deploys EKS+RDS+IAM); narrow if your CI does not need it."
}
