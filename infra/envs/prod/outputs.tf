output "eks_cluster_name" {
  description = "EKS cluster name (kubectl / aws eks update-kubeconfig)."
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value     = module.eks.cluster_endpoint
  sensitive = true
}

output "superset_rds_address" {
  description = "Superset metadata PostgreSQL endpoint."
  value       = module.superset_rds.db_instance_address
}

output "superset_rds_secret_arn" {
  description = "Secrets Manager ARN for the RDS master password."
  value       = module.superset_rds.secret_arn
}

output "eks_alb_controller_role_arn" {
  value = module.eks_alb_controller_identity.role_arn
}

output "ssm_bastion_instance_id" {
  description = "Start SSM port forwarding: aws ssm start-session --target <this-id> --document-name AWS-StartPortForwardingSessionToRemoteHost ..."
  value       = module.ssm_rds_bastion.instance_id
}

output "ssm_bastion_private_ip" {
  value = module.ssm_rds_bastion.private_ip
}
