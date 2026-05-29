output "repository_names" {
  description = "ECR repository names keyed by application image name."
  value       = { for name, repository in aws_ecr_repository.this : name => repository.name }
}

output "repository_arns" {
  description = "ECR repository ARNs keyed by application image name."
  value       = { for name, repository in aws_ecr_repository.this : name => repository.arn }
}

output "repository_urls" {
  description = "ECR repository URLs keyed by application image name."
  value       = { for name, repository in aws_ecr_repository.this : name => repository.repository_url }
}
