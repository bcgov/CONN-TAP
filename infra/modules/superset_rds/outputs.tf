output "db_instance_address" {
  value = aws_db_instance.superset.address
}

output "db_instance_port" {
  value = aws_db_instance.superset.port
}

output "db_name" {
  value = aws_db_instance.superset.db_name
}

output "db_username" {
  value = aws_db_instance.superset.username
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}

output "security_group_id" {
  value = aws_security_group.rds.id
}
