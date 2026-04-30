output "eks_cluster_name" {
  description = "EKS cluster name (kubectl / aws eks update-kubeconfig)."
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value     = module.eks.cluster_endpoint
  sensitive = true
}

output "rds_address" {
  description = "Platform PostgreSQL endpoint."
  value       = module.superset_rds.db_instance_address
}

output "rds_secret_arn" {
  description = "Secrets Manager ARN for the RDS master password."
  value       = module.superset_rds.secret_arn
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions to assume via OIDC. Set this as the role-to-assume in aws-actions/configure-aws-credentials."
  value       = module.github_actions_oidc.role_arn
}
