variable "aws_region" { type = string }
variable "account_id" { type = string }

# Existing LZA-test network
variable "vpc_id" { type = string }
variable "ec2_subnet_id" { type = string }

# EC2 (PowerBI desktop)
variable "powerbi_ami" { type = string }
variable "ec2_security_group_ids" { type = list(string) }

# Buckets created in LZA-test (must be globally unique names)
variable "ngta_raw_bucket" { type = string }
variable "tsma_raw_bucket" { type = string }
variable "tsma_ngta_mapping_bucket" { type = string }
variable "tsma_ngta_price_books_bucket" { type = string }

# Bucket where Glue scripts + Lambda zips live
variable "glue_assets_bucket" { type = string }

# Athena
variable "athena_results_prefix" {
  type    = string
  default = "athena_results/"
}

# Glue Catalog (Athena DBs)
variable "enable_glue_catalog_databases" {
  type    = bool
  default = true
}

# Redshift (optional in test; keep false unless explicitly needed)
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

# Use DATA subnets in LZA-test (Data-A + Data-B) if enabling Redshift
variable "redshift_subnet_ids" {
  type    = list(string)
  default = []
}

# Attach the DATA SG in LZA-test if enabling Redshift
variable "redshift_security_group_id" {
  type    = string
  default = ""
}

variable "enable_tsma_lambda_fact" {
  type    = bool
  default = false
}

# EC2 PowerBI instance (set false to skip if key/subnet issues)
variable "enable_ec2" {
  type    = bool
  default = true
}

# RDP access: CIDR to allow (e.g. office IP). Empty = use SSM port forwarding only (no direct RDP)
variable "ec2_rdp_allowed_cidr" {
  type        = string
  default     = ""
  description = "CIDR block to allow RDP (3389). Leave empty to use SSM port forwarding only."
}