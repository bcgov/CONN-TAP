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

output "rds_replica_addresses" {
  description = "Read replica endpoints (empty when no replicas are configured)."
  value       = module.platform_rds.replica_addresses
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

output "internal_ingress_group" {
  description = "Shared ALB ingress group for LZA internal load balancers."
  value       = local.internal_ingress_group
}

output "conn_tap_ingress_host" {
  description = "Frontend Ingress hostname on the internal ALB."
  value       = local.conn_tap_ingress_host
}

output "conn_tap_app_base_url" {
  description = "Public Stratus URL for the conn-tap frontend (APP_BASE_URL)."
  value       = local.conn_tap_app_base_url
}

output "web_subnet_ids_csv" {
  description = "Web-tier subnet IDs for ALB Ingress annotations."
  value       = local.web_subnet_ids_csv
}
