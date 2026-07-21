variable "name_prefix" {
  type        = string
  description = "Environment-scoped prefix for Lambda, IAM, and layer resource names (e.g. license-env)."
}

variable "ngta_raw_bucket_name" {
  type        = string
  description = "S3 bucket that receives raw Excel uploads."
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "RDS master password passed directly as a Lambda env var."
}

variable "rds_endpoint" {
  type        = string
  description = "RDS primary endpoint hostname."
}

variable "rds_db_name" {
  type    = string
  default = "app"
}

variable "rds_security_group_id" {
  type        = string
  description = "RDS security group ID. Lambda ingress rule on port 5432 is added to it."
}

variable "lambda_subnet_ids" {
  type        = list(string)
  description = "Data-tier subnet IDs for the VPC-attached Lambda."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID to attach the Lambda security group to."
}

variable "account_id" {
  type        = string
  description = "AWS account ID."
}

variable "repo_root" {
  type        = string
  description = "Absolute path to the repository root. Used to locate lambda/ and local_dev/ source files."
}

variable "dry_run" {
  type        = bool
  default     = false
  description = "When true, Lambda logs the S3 event but skips DB writes. Useful for testing."
}
