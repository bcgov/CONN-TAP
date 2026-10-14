variable "name_prefix" {
  type        = string
  description = "Prefix for resource names (e.g. license-env)."
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type        = string
  description = "Private subnet for the bastion (needs VPC path to SSM and to RDS, usually App tier)."
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "Bastion size; t3.micro is enough for SSM port forwarding."
}

variable "stop_schedule" {
  type        = string
  default     = "cron(0 19 * * ? *)"
  description = "EventBridge Scheduler expression to stop the bastion (daily 7 pm, so weekend manual starts are stopped too). Null disables."
}

variable "start_schedule" {
  type        = string
  default     = "cron(0 8 ? * MON-FRI *)"
  description = "EventBridge Scheduler expression to start the bastion (weekdays 8 am). Null leaves starting to manual."
}

variable "schedule_timezone" {
  type    = string
  default = "America/Vancouver"
}

variable "tags" {
  type    = map(string)
  default = {}
}
