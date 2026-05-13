variable "github_repositories" {
  type        = list(string)
  description = "GitHub repositories permitted to assume the role, in 'owner/repo' form (e.g. [\"bcgov/Data-Management-Platform\"])."

  validation {
    condition     = length(var.github_repositories) > 0
    error_message = "At least one repository in 'owner/repo' form is required."
  }
}

variable "allowed_subjects" {
  type        = list(string)
  default     = []
  description = <<-EOT
    Optional explicit list of token sub claims permitted (StringLike). Tighten the trust by
    branch/environment/tag, for example:
      ["repo:bcgov/Data-Management-Platform:ref:refs/heads/main",
       "repo:bcgov/Data-Management-Platform:environment:prod"]
    When empty, all workflows in github_repositories are allowed (repo:owner/repo:*).
  EOT
}

variable "role_name" {
  type        = string
  description = "IAM role name to create."
}

variable "managed_policy_arns" {
  type        = list(string)
  default     = []
  description = "AWS managed or customer managed policy ARNs to attach to the role."
}

variable "inline_policy_json" {
  type        = string
  default     = null
  description = "Optional inline policy JSON to attach to the role."
}

variable "max_session_duration" {
  type        = number
  default     = 3600
  description = "Maximum STS session duration in seconds (1h–12h). GitHub Actions tokens are short-lived; 1h is sufficient for most jobs."
}

variable "create_oidc_provider" {
  type        = bool
  default     = true
  description = "Create the account-level GitHub OIDC provider. Set false if one already exists in this AWS account (only one is permitted per account)."
}

variable "oidc_thumbprints" {
  type        = list(string)
  default     = ["6938fd4d98bab03faadb97b34396831e3780aea1", "1c58a3a8518e8759bf075b76b750d4f2df264fcd"]
  description = "Thumbprints for the GitHub OIDC issuer. AWS no longer strictly validates these but the field is required. Defaults cover the values published by GitHub."
}

variable "tags" {
  type    = map(string)
  default = {}
}
