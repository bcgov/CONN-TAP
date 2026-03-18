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

variable "ec2_key_name" {
  type        = string
  description = "Existing EC2 Key Pair name in AWS (create key pair manually in EC2 console or CLI)"
}