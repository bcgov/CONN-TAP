output "security_group_id" {
  description = "Attach this SG to RDS allow rules (or pass into postgres_rds allowed_security_group_ids)."
  value       = aws_security_group.bastion.id
}

output "instance_id" {
  description = "Use with aws ssm start-session and port-forwarding documents."
  value       = aws_instance.bastion.id
}

output "private_ip" {
  value = aws_instance.bastion.private_ip
}

output "schedule_names" {
  description = "EventBridge Scheduler schedules that stop/start the bastion."
  value       = concat(aws_scheduler_schedule.bastion_stop[*].name, aws_scheduler_schedule.bastion_start[*].name)
}
