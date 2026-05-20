variable "aws_region" {
  type = string
}

variable "env" {
  type = string
}

variable "ngta_raw_bucket_name" {
  type = string
}

variable "tsma_raw_bucket_name" {
  type = string
}

variable "mapping_bucket_name" {
  type = string
}

variable "price_books_bucket_name" {
  type = string
}

variable "glue_assets_bucket_name" {
  type = string
}

variable "vpc_name" {
  type = string
}

variable "ec2_subnet_name" {
  type = string
}

variable "ec2_security_group_names" {
  type = list(string)
}

variable "powerbi_key_name" {
  type = string
}

variable "ec2_public_key" {
  type = string
}

variable "powerbi_instance_name" {
  type = string
}

variable "powerbi_instance_type" {
  type = string
}

variable "powerbi_ami_id" {
  type = string
}

variable "assets_dir" {
  type = string
}

variable "account_id" {
  type = string
}

variable "powerbi_alert_email" {
  type        = string
  default     = null
  description = "Email address to receive alerts when the PowerBI EC2 instance has been running for more than 8 hours. Leave null to disable email alerts."
}

variable "lambda_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for VPC-attached Lambdas (use data-tier subnets that can reach RDS)."
  default     = []
}

variable "rds_security_group_id" {
  type        = string
  description = "Security group ID of the RDS instance. Lambda ingress rule is added to this SG."
  default     = ""
}

variable "rds_secret_arn" {
  type        = string
  description = "ARN of the Secrets Manager secret holding the RDS master password (plain string)."
  default     = ""
}

variable "rds_endpoint" {
  type        = string
  description = "Hostname of the RDS primary endpoint."
  default     = ""
}

variable "rds_db_name" {
  type        = string
  description = "Database name on the RDS instance."
  default     = "app"
}

variable "glue_job_max_concurrent_runs" {
  type        = number
  default     = 20
  description = "Maximum concurrent runs for all Glue jobs in this module. Increase if you expect many parallel triggers; decrease for stricter throttling."
}
