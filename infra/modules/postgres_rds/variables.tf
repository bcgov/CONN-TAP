variable "name_prefix" {
  type        = string
  description = "Short prefix for identifiers (e.g. license-env)."
}

variable "vpc_id" {
  type = string
}

variable "data_subnet_ids" {
  type        = list(string)
  description = "Data-tier subnet IDs (two AZs)."
}

variable "allowed_security_group_ids" {
  type        = map(string)
  description = <<-EOT
    Security groups allowed to reach PostgreSQL (typically EKS node, cluster, bastion).
    Keys must be static strings in configuration (not derived from the SG id) so for_each
    remains valid when values are known only after apply or during destroy planning.
  EOT
}

variable "engine_version" {
  type        = string
  default     = "16.14"
  description = "RDS PostgreSQL EngineVersion (must exist in the target region; see aws rds describe-db-engine-versions)."
}

variable "instance_class" {
  type    = string
  default = "db.t4g.small"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "db_name" {
  type    = string
  default = "app"
}

variable "username" {
  type    = string
  default = "dbadmin"
}

variable "skip_final_snapshot" {
  type    = bool
  default = true
}

variable "backup_retention_period" {
  type    = number
  default = 7
}

variable "storage_kms_key_id" {
  type        = string
  default     = null
  description = "KMS key ARN or ID for RDS storage encryption. If null, AWS uses the RDS-managed key for the account/region."
}

variable "multi_az" {
  type        = bool
  default     = false
  description = "Enable Multi-AZ deployment with a synchronous standby for HA. The standby is not readable; pair with read_replica_count for read scaling."
}

variable "deletion_protection" {
  type        = bool
  default     = false
  description = "Block accidental DB deletion. Recommended true for prod."
}

variable "read_replica_count" {
  type        = number
  default     = 0
  description = "Number of asynchronous read replicas to create alongside the primary. Replicas inherit the primary's instance class unless replica_instance_class is set."
}

variable "replica_instance_class" {
  type        = string
  default     = null
  description = "Instance class for read replicas. Defaults to the primary's instance_class when null."
}

variable "tags" {
  type    = map(string)
  default = {}
}
