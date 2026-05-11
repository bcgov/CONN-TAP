locals {
  github_repo_full = "${var.github_owner}/${var.github_repository}"

  # Prod defaults: only the main branch or the 'prod' GitHub Environment may
  # assume the role. Use a GitHub Environment with required reviewers + branch
  # protection on main for end-to-end gating.
  github_default_subjects = [
    "repo:${local.github_repo_full}:ref:refs/heads/main",
    "repo:${local.github_repo_full}:environment:prod",
  ]

  github_subjects = var.github_actions_allowed_subjects != null ? var.github_actions_allowed_subjects : local.github_default_subjects

  github_role_name = coalesce(var.github_actions_role_name, "${var.license}-${var.env}-github-actions")
}

module "github_actions_oidc" {
  source = "../../modules/github_actions_oidc"

  github_repositories  = [local.github_repo_full]
  allowed_subjects     = local.github_subjects
  role_name            = local.github_role_name
  managed_policy_arns  = var.github_actions_managed_policy_arns
  create_oidc_provider = var.github_actions_create_oidc_provider

  tags = {
    Environment = var.env
    License     = var.license
  }
}
