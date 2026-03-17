variable "aws_region" {
  type = string
}

variable "license" {
  type        = string
  description = "License plate prefix used to namespace all resource names (e.g. abc123)."
}

variable "env" {
  type = string
}

variable "ec2_security_group_names" {
  type        = list(string)
  default     = ["App"]
  description = "Security groups to attach to the PowerBI EC2 instance. Defaults to [\"App\"]. Override if additional groups are needed."
}

variable "powerbi_instance_type" {
  type        = string
  default     = "t3.large"
  description = "EC2 instance type for the PowerBI Desktop instance. Defaults to t3.large. Override for different sizing."
}

variable "powerbi_ami_id" {
  type    = string
  default = "ami-067abc25c5d2e14af"
}

variable "assets_dir" {
  type        = string
  default     = "../../.."
  description = "Path to the repo root containing the scripts/ and lambda/ folders, relative to the environment directory. Defaults to ../../.. Override if running terraform from a different working directory."
}

variable "account_id" {
  type    = string
  default = null
}

variable "powerbi_alert_email" {
  type        = string
  default     = null
  description = "Email to receive alerts when PowerBI EC2 has been running > 8 hours. Leave unset to disable."
}
