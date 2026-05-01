output "db_instance_address" {
  value = aws_db_instance.primary.address
}

output "db_instance_port" {
  value = aws_db_instance.primary.port
}

output "db_name" {
  value = aws_db_instance.primary.db_name
}

output "db_username" {
  value = aws_db_instance.primary.username
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}

output "security_group_id" {
  value = aws_security_group.rds.id
}

output "replica_addresses" {
  description = "List of read replica endpoints (empty when read_replica_count = 0)."
  value       = aws_db_instance.replica[*].address
}
