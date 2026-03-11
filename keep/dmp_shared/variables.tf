variable "aws_region" { type = string }
variable "account_id" { type = string }

variable "vpc_id" { type = string }
variable "ec2_subnet_id" { type = string }

variable "powerbi_ami" { type = string }
variable "powerbi_key_name" { type = string }
variable "ec2_security_group_ids" { type = list(string) }

variable "ngta_raw_bucket" { type = string }
variable "tsma_raw_bucket" { type = string }
variable "tsma_ngta_mapping_bucket" { type = string }
variable "tsma_ngta_price_books_bucket" { type = string }

variable "glue_assets_bucket" { type = string }

variable "athena_results_prefix" {
  type    = string
  default = "athena_results/"
}

# Glue Catalog (Athena DBs)
variable "enable_glue_catalog_databases" {
  type    = bool
  default = true
}

# Redshift (optional)
variable "enable_redshift" {
  type    = bool
  default = false
}

variable "redshift_cluster_identifier" {
  type    = string
  default = "bc-redshift-cluster"
}

variable "redshift_node_type" {
  type    = string
  default = "dc2.large"
}

variable "redshift_database_name" {
  type    = string
  default = "dev"
}

variable "redshift_master_username" {
  type    = string
  default = "adminuser"
}

variable "redshift_subnet_ids" {
  type    = list(string)
  default = []
}

variable "redshift_security_group_id" {
  type    = string
  default = ""
}

variable "enable_tsma_lambda_fact" {
  type    = bool
  default = false
}

variable "ec2_name" {
  type        = string
  description = "Name tag for the PowerBI EC2"
  default     = "ec2-powerbi-desktop"
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.large"
}

variable "ec2_root_volume_gb" {
  type    = number
  default = 50
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

variable "assets_local_dir" {
  type        = string
  description = "Path to folder containing subfolders: lambda/ and scripts/ (for Terraform upload)"
}