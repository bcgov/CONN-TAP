output "role_arn" {
  description = "ARN of the IAM role for GitHub Actions to assume."
  value       = aws_iam_role.github_actions.arn
}

output "role_name" {
  value = aws_iam_role.github_actions.name
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC identity provider used by the trust policy."
  value       = local.provider_arn
}
