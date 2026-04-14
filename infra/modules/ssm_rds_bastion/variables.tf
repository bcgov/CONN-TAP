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

variable "tags" {
  type    = map(string)
  default = {}
}
