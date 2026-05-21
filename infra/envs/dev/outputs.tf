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
  value       = module.platform_rds.db_instance_address
}

output "rds_secret_arn" {
  description = "Secrets Manager ARN for the RDS master password."
  value       = module.platform_rds.secret_arn
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions to assume via OIDC. Set this as the role-to-assume in aws-actions/configure-aws-credentials."
  value       = module.github_actions_oidc.role_arn
}

output "app_ecr_repository_urls" {
  description = "ECR repository URLs for application images."
  value       = module.app_ecr.repository_urls
}

output "postgres_bastion_instance_id" {
  description = "Use with: aws ssm start-session --target <id> --document-name AWS-StartPortForwardingSessionToRemoteHost"
  value       = module.postgres_bastion.instance_id
}

output "postgres_bastion_private_ip" {
  value = module.postgres_bastion.private_ip
}
