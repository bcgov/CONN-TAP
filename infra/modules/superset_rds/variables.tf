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
  default     = "16.6"
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
  default = "superset"
}

variable "username" {
  type    = string
  default = "superset"
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

variable "tags" {
  type    = map(string)
  default = {}
}
