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

output "rds_replica_addresses" {
  description = "Read replica endpoints (empty when no replicas are configured)."
  value       = module.superset_rds.replica_addresses
}
