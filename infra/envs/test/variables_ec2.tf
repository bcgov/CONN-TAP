variable "ec2_name" {
  type        = string
  description = "Name tag for the PowerBI EC2"
  default     = "ec2-powerbi-desktop"
}

variable "ec2_instance_type" {
  type        = string
  default     = "t3.large"
}

variable "ec2_root_volume_gb" {
  type        = number
  default     = 50
}

variable "ec2_instance_profile_name" {
  type        = string
  description = "Existing IAM Instance Profile name to attach to EC2 (or manage via Terraform separately)"
}

variable "ec2_key_name" {
  type        = string
  description = "EC2 Key Pair name to use in the new LZA account"
}

variable "ec2_public_key" {
  type        = string
  description = "Public key material for the EC2 key pair"
  sensitive   = true
}